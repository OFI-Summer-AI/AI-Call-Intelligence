"""
Recordings API -- lists and serves final pipeline reports, enriched for the
React frontend's data contract (extracted_fields carries conformance/call scores).
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse, Response

from app.config import UPLOAD_DIR, REPORTS_FINAL_DIR, OUTPUT_DIR
from app.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# In-memory job status store (reset on server restart -- acceptable for short-lived jobs)
_processing_jobs: Dict[str, dict] = {}


# -- Adapter: enrich extracted_fields with call_quality_report scores ---------

def _conformance_status(score: float | int | None) -> str:
    if score is None:
        return ""
    s = float(score)
    if s >= 85:
        return "pass"
    if s >= 65:
        return "review"
    return "fail"


def _enrich_for_frontend(rec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Copy scores from call_quality_report into extracted_fields so the React
    UI (which reads rec.extracted_fields.*) works without changes.
    """
    cqr = rec.get("call_quality_report") or {}
    polished = rec.get("polished_transcript") or {}
    ef = dict(rec.get("extracted_fields") or {})

    # Conformance score
    conf_score = cqr.get("conformance_score_0_100")
    if conf_score is not None and ef.get("conformance_score") is None:
        ef["conformance_score"] = conf_score
    if ef.get("conformance_status") is None:
        ef["conformance_status"] = _conformance_status(ef.get("conformance_score"))

    # Call summary -- prefer polished overview, fall back to call_level_summary
    if not ef.get("call_summary"):
        ef["call_summary"] = (
            polished.get("meeting_overview")
            or cqr.get("call_level_summary")
            or rec.get("summary")
            or ""
        )

    # Insights and next actions from call quality report
    if not ef.get("call_insights"):
        ef["call_insights"] = cqr.get("insights") or []
    if not ef.get("next_steps"):
        ef["next_steps"] = ef.get("next_steps") or cqr.get("next_actions") or []

    # Conclusions
    if not ef.get("conclusions"):
        ef["conclusions"] = cqr.get("conclusion") or cqr.get("conclusions") or ""

    rec = dict(rec)
    rec["extracted_fields"] = ef
    return rec


# -- Load helpers -------------------------------------------------------------

def _load_final_reports() -> List[Dict[str, Any]]:
    """Return all records from data/reports/final/, newest first."""
    results: List[Dict[str, Any]] = []
    for p in sorted(REPORTS_FINAL_DIR.glob("*_final_report.json"),
                    key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
            results.append(_enrich_for_frontend(rec))
        except Exception as exc:
            logger.warning("Could not load %s: %s", p.name, exc)
    return results


def _load_legacy_results() -> List[Dict[str, Any]]:
    """Fallback: load older *_result.json files from data/outputs/."""
    results: List[Dict[str, Any]] = []
    for p in sorted(OUTPUT_DIR.glob("*_result.json"),
                    key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
            results.append(_enrich_for_frontend(rec))
        except Exception:
            pass
    return results


def _get_job_id_set(records: List[Dict[str, Any]]) -> set[str]:
    return {r.get("job_id", "") for r in records}


# -- Endpoints ----------------------------------------------------------------

@router.get("/api/recordings")
async def list_recordings():
    final = _load_final_reports()
    legacy = _load_legacy_results()
    seen = _get_job_id_set(final)
    combined = final + [r for r in legacy if r.get("job_id", "") not in seen]
    return combined


@router.get("/api/recordings/{job_id}")
async def get_recording(job_id: str):
    final_path = REPORTS_FINAL_DIR / f"{job_id}_final_report.json"
    if final_path.exists():
        rec = json.loads(final_path.read_text(encoding="utf-8"))
        return _enrich_for_frontend(rec)
    legacy_path = OUTPUT_DIR / f"{job_id}_result.json"
    if legacy_path.exists():
        rec = json.loads(legacy_path.read_text(encoding="utf-8"))
        return _enrich_for_frontend(rec)
    return JSONResponse({"error": "not found"}, status_code=404)


@router.post("/api/recordings/{job_id}/reanalyze")
async def reanalyze_recording(job_id: str):
    """Re-run LLM assessment on existing transcript (skips audio/STT stages)."""
    final_path = REPORTS_FINAL_DIR / f"{job_id}_final_report.json"
    legacy_path = OUTPUT_DIR / f"{job_id}_result.json"

    if not final_path.exists() and not legacy_path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)

    source_path = final_path if final_path.exists() else legacy_path
    data = json.loads(source_path.read_text(encoding="utf-8"))
    transcript = data.get("transcript") or data.get("segments") or []

    from app.services.field_extractor import FieldExtractor
    from app.services.risk_report_service import RiskReportService
    from app.services.call_assessment_report_service import CallAssessmentReportService
    from app.services.storage_service import StorageService

    storage = StorageService()
    extracted_fields = FieldExtractor().extract(transcript)
    risk_report = RiskReportService().generate(extracted_fields, transcript)
    assessment_pkg = CallAssessmentReportService().build(transcript, extracted_fields)

    data["extracted_fields"] = extracted_fields
    data["risk_report"] = risk_report
    data["polished_transcript"] = assessment_pkg["polished_transcript"]
    data["topic_wise_summary"] = assessment_pkg.get("topic_wise_summary") or []
    data["question_coverage"] = assessment_pkg["question_coverage"]
    data["call_quality_report"] = assessment_pkg["call_quality_report"]

    storage.save_json(data, source_path)
    return _enrich_for_frontend(data)


@router.get("/api/recordings/{job_id}/pdf")
async def download_pdf(job_id: str):
    final_path = REPORTS_FINAL_DIR / f"{job_id}_final_report.json"
    legacy_path = OUTPUT_DIR / f"{job_id}_result.json"
    source_path = final_path if final_path.exists() else (legacy_path if legacy_path.exists() else None)
    if source_path is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    rec = json.loads(source_path.read_text(encoding="utf-8"))
    rec = _enrich_for_frontend(rec)
    pdf_bytes = _generate_pdf(rec)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={job_id.replace(' ', '_')}_report.pdf"},
    )


# -- Upload + process ---------------------------------------------------------

@router.api_route("/api/process", methods=["GET", "POST"])
async def process_file(background_tasks: BackgroundTasks, filename: str):
    job_id = re.sub(r"[^\w\-]", "_", Path(filename).stem)
    if _processing_jobs.get(job_id, {}).get("status") == "processing":
        return {"job_id": job_id, "status": "already_processing"}
    _processing_jobs[job_id] = {"status": "processing", "started": datetime.now().isoformat()}
    background_tasks.add_task(_run_pipeline_bg, filename, job_id)
    return {"job_id": job_id, "status": "processing"}


@router.get("/api/process-status/{job_id}")
async def process_status(job_id: str):
    final_path = REPORTS_FINAL_DIR / f"{job_id}_final_report.json"
    if final_path.exists():
        return {"status": "done"}
    legacy_path = OUTPUT_DIR / f"{job_id}_result.json"
    if legacy_path.exists():
        return {"status": "done"}
    return _processing_jobs.get(job_id, {"status": "not_found"})


def _run_pipeline_bg(filename: str, job_id: str) -> None:
    try:
        src = UPLOAD_DIR / filename
        if not src.exists():
            _processing_jobs[job_id] = {"status": "error", "error": f"File not found: {filename}"}
            return
        from app.pipeline.pipeline import Pipeline
        Pipeline().run(str(src))
        _processing_jobs[job_id] = {"status": "done"}
    except Exception as e:
        logger.error("Pipeline failed for %s: %s", job_id, e)
        _processing_jobs[job_id] = {"status": "error", "error": str(e)}


# -- PDF generation -----------------------------------------------------------

def _generate_pdf(rec: Dict[str, Any]) -> bytes:
    import io as _io
    from fpdf import FPDF
    from fpdf.enums import WrapMode, XPos, YPos

    from app.services.pdf_chart_helpers import distinct_speakers
    from app.services.pdf_figures import build_intelligence_pngs
    from app.services.pdf_intel import (
        cq_conclusion_text, cq_insights_list, filtered_insights,
        merge_next_steps, missing_discussion_areas, narrative_opening,
        smart_quote_highlights, strategic_assessment_bullets,
        tactical_client_signals, topic_importance_matrix,
    )
    from app.services.pdf_narrative import (
        budget_label, compliance_mentions, decision_clarity_label,
        engagement_label, executive_bullets, format_duration_hms,
        guess_meeting_datetime, pain_points_from_polished,
        parse_polished_list, recommendation_banner_text, risk_severity_prefix,
    )

    def _l1(text: str, limit: int = 12000) -> str:
        t = str(text).replace("\r\n", "\n").strip()
        if len(t) > limit:
            t = t[:limit - 3] + "..."
        return t.encode("latin-1", errors="replace").decode("latin-1")

    class _BriefPDF(FPDF):
        def footer(self) -> None:
            self.set_y(-12)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 8, _l1(f"Page {self.page_no()}", 40), align="C")

    def _maybe_new_page(pdf: FPDF, min_y: float) -> None:
        if pdf.get_y() > min_y:
            pdf.add_page()

    def _image_row(pdf: FPDF, png: bytes, max_h_mm: float = 76.0) -> None:
        _maybe_new_page(pdf, 235)
        y0 = pdf.get_y()
        pdf.image(_io.BytesIO(png), x=pdf.l_margin, y=y0, w=pdf.epw, h=max_h_mm)
        pdf.set_y(y0 + max_h_mm + 8)

    def _hero_bar(pdf: FPDF) -> None:
        y = pdf.get_y()
        pdf.set_fill_color(49, 46, 129)
        pdf.rect(pdf.l_margin, y, pdf.epw, 10, style="F")
        pdf.set_xy(pdf.l_margin + 2, y + 2.5)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 5, _l1("AI business meeting analyst", 80))
        pdf.set_text_color(0, 0, 0)
        pdf.set_y(y + 13)

    def _heading(pdf: FPDF, text: str, size: int = 13, rgb: tuple = (30, 27, 75)) -> None:
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", size)
        pdf.set_text_color(*rgb)
        pdf.multi_cell(pdf.epw, 7.5, _l1(text, 200), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(1.5)

    def _subheading(pdf: FPDF, text: str) -> None:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(71, 85, 105)
        pdf.multi_cell(pdf.epw, 6, _l1(text, 160), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(1)

    def _body(pdf: FPDF, text: str, h: float = 5.6, limit: int = 6000) -> None:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pdf.epw, h, _l1(text, limit), wrapmode=WrapMode.WORD, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def _kpi_table(pdf: FPDF, rows: list) -> None:
        w_label = pdf.epw * 0.52
        w_val = pdf.epw * 0.48
        row_h = 9.0
        fills = ((239, 246, 255), (236, 253, 245), (254, 252, 232), (254, 243, 199), (252, 231, 243), (224, 231, 255))
        for i, (lab, val) in enumerate(rows):
            pdf.set_fill_color(*fills[i % len(fills)])
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(w_label, row_h, _l1(lab, 72), border=1, fill=True)
            pdf.set_font("Helvetica", "", 10.5)
            pdf.cell(w_val, row_h, _l1(val, 96), border=1, ln=1, fill=True)
        pdf.ln(2)

    def _banner(pdf: FPDF, text: str) -> None:
        pdf.ln(4)
        y = pdf.get_y()
        pdf.set_fill_color(224, 231, 255)
        pdf.set_draw_color(79, 70, 229)
        pdf.rect(pdf.l_margin, y, pdf.epw, 20, style="DF")
        pdf.set_xy(pdf.l_margin + 3, y + 4)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.multi_cell(pdf.epw - 6, 6.2, _l1(text, 520), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_y(y + 22)

    def _data_table(pdf: FPDF, headers: list, rows: list, col_widths: list) -> None:
        hdr_h = 8.0
        row_h = 8.0
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(226, 232, 240)
        for h, w in zip(headers, col_widths):
            t = str(h)[:int(w / 1.45)]
            pdf.cell(w, hdr_h, _l1(t, 100), border=1, fill=True)
        pdf.ln()
        pdf.set_font("Helvetica", "", 9)
        for row in rows:
            for cell, w in zip(row, col_widths):
                mc = max(24, int(w / 1.2) + 12)
                t = str(cell)
                if len(t) > mc:
                    t = t[:mc - 1] + "."
                pdf.cell(w, row_h, _l1(t, 800), border=1)
            pdf.ln()
        pdf.ln(2)

    def _discovery_blocks(pdf: FPDF, cov: list, max_items: int = 12) -> None:
        rows_in = [r for r in cov if isinstance(r, dict)]
        if not rows_in:
            _body(pdf, "No discovery checklist rows in this export.", limit=400)
            return
        _body(pdf, "Each block is one checklist question from your pipeline, with capture status, model notes, and evidence.", limit=420)
        pdf.ln(3)
        for i, row in enumerate(rows_in[:max_items]):
            q = str(row.get("title", row.get("id", "?"))).strip()
            st = str(row.get("status", "")).replace("_", " ").strip().title()
            conf_str = str(row.get("confidence", "")).strip().title()
            status_line = f"{st} ({conf_str})" if conf_str else st
            notes = str(row.get("notes", "") or "").strip() or "--"
            ev = str(row.get("evidence", "") or "").strip() or "--"
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(30, 41, 59)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 6.5, _l1(q, 1400), wrapmode=WrapMode.WORD, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 10)
            block = f"Status: {status_line}\n\nNotes\n{notes}\n\nEvidence\n{ev}"
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 5.6, _l1(block, 5200), wrapmode=WrapMode.WORD, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(6 if i < min(len(rows_in), max_items) - 1 else 3)

    def _actions_table(pdf: FPDF, actions: list) -> None:
        headers = ["Action", "Owner", "Urgency", "Status"]
        w = [pdf.epw * 0.48, pdf.epw * 0.18, pdf.epw * 0.17, pdf.epw * 0.17]
        rows = []
        for i, act in enumerate(actions[:12]):
            urg = "High" if i < 2 else "Medium"
            rows.append((act, "TBD (assign in CRM)", urg, "Pending"))
        _data_table(pdf, headers, rows, w)

    # Gather data
    data = rec
    ef = data.get("extracted_fields") or {}
    cq = data.get("call_quality_report") or {}
    pt = data.get("polished_transcript") or {}
    if not isinstance(pt, dict):
        pt = {}
    transcript = data.get("transcript") or []
    topics = data.get("topic_wise_summary") or []
    cov = data.get("question_coverage") if isinstance(data.get("question_coverage"), list) else []
    risk = data.get("risk_report") or {}
    rlist = [str(x).strip() for x in (risk.get("risks") or []) if str(x).strip()]

    job_id = str(data.get("job_id", "recording"))
    title = re.sub(r"_\d{4}-\d{2}-\d{2}T[\d\-]+$", "", job_id).replace("_", " ").title()
    client = str(ef.get("client_name") or "--")
    when = guess_meeting_datetime(job_id)
    duration = format_duration_hms(data)
    participants = distinct_speakers(transcript)
    meeting_type = "Uploaded recording"

    eff = cq.get("conformance_score_0_100")
    if isinstance(eff, (int, float)):
        eff_s = f"{int(round(float(eff)))}%"
    else:
        conf_obj = cq.get("conformance") or {}
        sc = conf_obj.get("score_0_100") if isinstance(conf_obj, dict) else None
        eff_s = f"{int(sc)}%" if isinstance(sc, (int, float)) else "--"

    actions = [str(a).strip() for a in (cq.get("next_actions") or []) if str(a).strip()]
    merged_steps = merge_next_steps(actions, pt)
    insights_list = cq_insights_list(cq)
    concl_text = cq_conclusion_text(cq)
    pending_areas = missing_discussion_areas(cov)
    participant_tile = "Needs speaker IDs" if participants == 0 else str(participants)
    n_themes = len(topics) if isinstance(topics, list) else 0
    matrix_rows = topic_importance_matrix(topics if isinstance(topics, list) else [], transcript)

    try:
        pngs = build_intelligence_pngs(data)
    except Exception as e:
        logger.warning("PDF chart generation failed: %s", e)
        pngs = {}

    # Build PDF
    pdf = _BriefPDF(format="A4", unit="mm")
    pdf.set_margins(16, 16, 16)
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()

    _hero_bar(pdf)
    pdf.set_font("Helvetica", "B", 15)
    pdf.multi_cell(pdf.epw, 8, _l1("Executive AI Meeting Intelligence Brief", 120))
    pdf.set_font("Helvetica", "B", 11.5)
    pdf.set_text_color(51, 65, 85)
    pdf.multi_cell(pdf.epw, 6.5, _l1(title, 200))
    pdf.set_text_color(0, 0, 0)
    meta_lines = [
        f"Client: {client}",
        f"Reference time (from file name): {when}",
        f"Duration: {duration}",
        f"Distinct speaker labels: {participants if participants else '--'}",
        f"Meeting type: {meeting_type}",
    ]
    _body(pdf, "\n".join(meta_lines), limit=800)

    _heading(pdf, "Executive snapshot", size=12)
    _kpi_table(pdf, [
        ("Meeting effectiveness (checklist)", eff_s),
        ("Engagement (tone proxy)", engagement_label(data)),
        ("Action items captured (merged)", str(len(merged_steps))),
        ("Risks / watch-outs", str(len(rlist))),
        ("Budget discussed", budget_label(ef, cq)),
        ("Decision clarity (proxy)", decision_clarity_label(cq)),
    ])
    _subheading(pdf, "Signal counts (matches product dashboard header)")
    _kpi_table(pdf, [
        ("Insights on call", str(len(insights_list))),
        ("Next actions (merged list)", str(len(merged_steps))),
        ("Participant scorecards", participant_tile),
        ("Open discovery gaps", str(len(pending_areas))),
        ("Watch-out flags", str(len(rlist))),
        ("Theme groups", str(n_themes)),
    ])

    _subheading(pdf, "What happened (one narrative)")
    _body(pdf, narrative_opening(pt, str(data.get("summary") or "")), limit=1100)

    _heading(pdf, "Executive bullets", size=11)
    bullets = executive_bullets(str(data.get("summary") or ""), max_n=5)
    if bullets:
        for b in bullets:
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(pdf.epw, 5.6, _l1(f"- {b}", 600), wrapmode=WrapMode.WORD, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1.5)
    else:
        _body(pdf, "(No packaged summary.)")

    _banner(pdf, recommendation_banner_text(cq))

    # Visual intelligence
    if pngs:
        pdf.add_page()
        _heading(pdf, "Meeting intelligence (visual)", size=12)
        _body(pdf, "Speaker heatmap (who was active over time), sentiment proxy, momentum by meeting segment, and topic depth (relative, from model topic summaries).", limit=420)
        if "speaker_timeline" in pngs:
            _image_row(pdf, pngs["speaker_timeline"], 48)
        if "sentiment" in pngs:
            _image_row(pdf, pngs["sentiment"], 38)
        pdf.add_page()
        if "momentum" in pngs:
            _image_row(pdf, pngs["momentum"], 34)
        if "topic_depth" in pngs:
            _image_row(pdf, pngs["topic_depth"], 34)

    # Topic importance matrix
    pdf.add_page()
    _heading(pdf, "AI topic importance matrix", size=12)
    _body(pdf, "Importance and depth are heuristics from topic summaries and transcript overlap; sentiment reads topic wording.", limit=320)
    hdr = ["Topic", "Importance", "Sentiment", "Depth"]
    cw = [pdf.epw * 0.40, pdf.epw * 0.20, pdf.epw * 0.20, pdf.epw * 0.20]
    _data_table(pdf, hdr, matrix_rows, cw)

    # Business insights
    pdf.add_page()
    _heading(pdf, "Business insights", size=12)
    _subheading(pdf, "Client pain signals")
    pains = pain_points_from_polished(pt)
    if pains:
        for i, p in enumerate(pains, 1):
            _body(pdf, f"{i}. {p}", limit=500)
    else:
        _body(pdf, "No structured pain fields.")

    _subheading(pdf, "Client signals (meeting-specific)")
    sigs = tactical_client_signals(cq, pt, transcript, topics if isinstance(topics, list) else [], cov)
    if sigs:
        for s in sigs:
            _body(pdf, f"- {s}", limit=700)
    else:
        _body(pdf, "Add question_coverage + richer transcript for stronger signals.")

    _subheading(pdf, "AI observations (non-generic)")
    fins = filtered_insights(cq)
    if fins:
        for x in fins:
            _body(pdf, f"- {x}", limit=650)
    else:
        _body(pdf, "(Filtered empty -- see call quality in product.)")

    _subheading(pdf, "Risks and blockers")
    if rlist:
        for r in rlist[:10]:
            _body(pdf, f"{risk_severity_prefix(r)}{r}", limit=500)
    else:
        _body(pdf, "No risk bullets.")

    # Discovery checklist
    pdf.add_page()
    _heading(pdf, "Discovery checklist (questions, status, answers)", size=12)
    _discovery_blocks(pdf, cov)

    _heading(pdf, "What was not fully nailed", size=11)
    if pending_areas:
        _body(pdf, "Gaps to close in follow-up:\n" + "\n".join(f"- {m}" for m in pending_areas), limit=500)
    else:
        _body(pdf, "No checklist gaps flagged (or checklist not in this export).")

    # Action center
    pdf.add_page()
    _heading(pdf, "Action center", size=12)
    _subheading(pdf, "Written conclusion from analysis")
    _body(pdf, concl_text or "No conclusion block on this export.", limit=4500)
    _subheading(pdf, "Next steps (assign owners in your system of record)")
    if merged_steps:
        _actions_table(pdf, merged_steps)
    else:
        _body(pdf, "No next_actions or polished next_steps on this export.", limit=120)

    _subheading(pdf, "Decisions / commitments")
    decs = parse_polished_list(pt.get("next_steps"))
    if decs:
        for d in decs[:12]:
            _body(pdf, f"[Commitment] {d}", limit=400)
    else:
        _body(pdf, "No parsed polished next_steps.")

    _subheading(pdf, "Timeline signal")
    tl = str(ef.get("timeline") or pt.get("timeline") or "").strip()
    _body(pdf, tl or "(Not captured.)", limit=600)

    # Technical snapshot
    pdf.add_page()
    _heading(pdf, "Technical snapshot", size=12)
    _tp = ef.get("techstack_platform") or []
    techs = _tp if isinstance(_tp, list) else [str(_tp)] if _tp else []
    if techs:
        _body(pdf, "Systems / platforms:\n- " + "\n- ".join(str(t) for t in techs[:22]), limit=1200)
    else:
        td = str(pt.get("technical_details") or "").strip()
        _body(pdf, td[:1400] if td else "No platform list.", limit=1600)
    _subheading(pdf, "Compliance themes (inferred)")
    cm = compliance_mentions(ef, rlist)
    _body(pdf, "\n".join(f"- {c}" for c in cm) if cm else "--", limit=400)

    # Strategic assessment
    pdf.add_page()
    _heading(pdf, "Strategic AI assessment", size=12)
    _body(pdf, "Synthesized only from structured assessment fields (no new model call). Use as internal exec read - validate commercially before client send.", limit=280)
    for line in strategic_assessment_bullets(cq, ef, risk):
        _body(pdf, f"- {line}", limit=500)

    # Key quotes
    pdf.add_page()
    _heading(pdf, "Key quotes (evidence)", size=11)
    hl = smart_quote_highlights(transcript, max_n=5)
    if hl:
        for quote in hl:
            _body(pdf, quote, limit=500, h=6.0)
            pdf.ln(2)
    else:
        _body(pdf, "No high-signal quotes auto-selected.", limit=200)
    _body(pdf, "The full call transcript is intentionally omitted from this PDF. Export the meeting JSON from the product when you need every line.", limit=320)

    out = pdf.output()
    if isinstance(out, str):
        return out.encode("latin-1")
    return bytes(out)
