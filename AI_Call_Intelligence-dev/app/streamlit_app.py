"""
AI Call Intelligence — Main UI
Run: streamlit run app/streamlit_app.py  (from AI_Call_Intelligence-dev/)
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# ensure project root is on path regardless of cwd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.config import OUTPUT_DIR, UPLOAD_DIR, AUDIO_DIR, WHISPER_MODEL_SIZE

REQ_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "requirements"
REQ_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

FASTAPI_URL = "http://localhost:8000"
WS_URL      = "ws://localhost:8000/ws/transcribe"

SUPPORTED_UPLOAD_EXTS = ["mp4", "webm", "mkv", "mov", "avi", "wav", "mp3", "m4a"]
REQ_MODELS = [
    "groq/llama-3.1-8b-instant",
    "groq/llama3-70b-8192",
    "groq/mixtral-8x7b-32768",
    "gpt-4o",
    "ollama/mistral",
]

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Call Intelligence",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ══ BASE ══════════════════════════════════════════════════════════════════ */
footer,header,#MainMenu { display:none!important; }
[data-testid="stAppViewContainer"],
[data-testid="stMain"] { background:#ffffff!important; }
body, .stApp, [data-testid="stAppViewContainer"] * { color:#111111; }

/* ══ SIDEBAR ═══════════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
  background:#f5f5f5!important;
  border-right:1px solid #e0e0e0!important;
}
/* Keep sidebar always expanded — hide only the close button, not the re-open arrow */
[data-testid="stSidebarCollapseButton"] { display:none!important; }
[data-testid="stSidebar"] { transform:none!important; min-width:244px!important; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div { color:#333333; }

[data-testid="stSidebar"] [data-testid="stRadio"] > div { gap:2px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label {
  color:#333333!important; border-radius:6px; padding:10px 14px;
  font-size:.875rem; font-weight:500; cursor:pointer;
  border:1px solid transparent; letter-spacing:.3px;
  transition: all .18s;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
  background:#eeeeee!important; color:#a07830!important;
  border-color:rgba(201,168,76,.25)!important;
}
[data-testid="stSidebar"] .stButton button {
  background:#ffffff!important; color:#333333!important;
  border:1px solid #e0e0e0!important; border-radius:7px!important;
  font-size:.82rem!important; transition:all .18s!important;
}
[data-testid="stSidebar"] .stButton button:hover {
  color:#a07830!important;
  border-color:rgba(201,168,76,.5)!important;
}

/* ══ CONTENT AREA ══════════════════════════════════════════════════════════ */
[data-testid="stVerticalBlockBorderWrapper"] {
  background:#f9f9f9!important;
  border:1px solid #e0e0e0!important;
  border-radius:10px!important;
  box-shadow:0 2px 8px rgba(0,0,0,.06)!important;
  transition:border-color .2s, box-shadow .2s!important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color:rgba(201,168,76,.4)!important;
  box-shadow:0 4px 24px rgba(201,168,76,.08)!important;
}

/* ══ TYPOGRAPHY ════════════════════════════════════════════════════════════ */
.card-title { font-size:1rem; font-weight:600; color:#111111; line-height:1.35; }
.card-meta  { font-size:.75rem; color:#666666; margin-top:5px; letter-spacing:.3px; }

.sec-label {
  font-size:.6rem; font-weight:800; letter-spacing:2px;
  text-transform:uppercase; color:#a07830; margin-bottom:14px;
  padding-bottom:8px; border-bottom:1px solid #e0e0e0;
}

/* ══ STAT BOXES ════════════════════════════════════════════════════════════ */
.stat-box {
  background:#f9f9f9; border:1px solid #e0e0e0; border-radius:10px;
  padding:18px 12px; text-align:center;
  transition:border-color .2s, box-shadow .2s;
}
.stat-box:hover {
  border-color:rgba(201,168,76,.5);
  box-shadow:0 0 22px rgba(201,168,76,.12);
}
.stat-num { font-size:1.7rem; font-weight:800; line-height:1; color:#111111; }
.stat-lbl { font-size:.6rem; color:#666666; margin-top:6px; font-weight:700;
            letter-spacing:1.3px; text-transform:uppercase; }

/* ══ CHIPS ═════════════════════════════════════════════════════════════════ */
.chip {
  display:inline-block; background:#fdf8ee; color:#a07830;
  border:1px solid rgba(201,168,76,.4); border-radius:4px;
  padding:3px 10px; font-size:.7rem; font-weight:600;
  margin:2px 3px 2px 0; letter-spacing:.3px;
}
.chip-green { background:#f0fff4; color:#16a34a; border-color:rgba(74,222,128,.4); }

/* ══ TIER / CONFIDENCE BADGES ══════════════════════════════════════════════ */
.tier-v { background:#f0fff4;color:#16a34a;border:1px solid rgba(74,222,128,.3);border-radius:4px;padding:2px 9px;font-size:.67rem;font-weight:700;letter-spacing:.5px; }
.tier-a { background:#fffbeb;color:#d97706;border:1px solid rgba(251,191,36,.3);border-radius:4px;padding:2px 9px;font-size:.67rem;font-weight:700;letter-spacing:.5px; }
.tier-u { background:#fff5f5;color:#dc2626;border:1px solid rgba(248,113,113,.3);border-radius:4px;padding:2px 9px;font-size:.67rem;font-weight:700;letter-spacing:.5px; }

.badge-g { display:inline-block;padding:4px 12px;border-radius:4px;font-size:.7rem;font-weight:700;background:#f0fff4;color:#16a34a;border:1px solid rgba(74,222,128,.3);letter-spacing:.4px; }
.badge-y { display:inline-block;padding:4px 12px;border-radius:4px;font-size:.7rem;font-weight:700;background:#fffbeb;color:#d97706;border:1px solid rgba(251,191,36,.3);letter-spacing:.4px; }
.badge-r { display:inline-block;padding:4px 12px;border-radius:4px;font-size:.7rem;font-weight:700;background:#fff5f5;color:#dc2626;border:1px solid rgba(248,113,113,.3);letter-spacing:.4px; }

/* ══ RIGHT PANEL ═══════════════════════════════════════════════════════════ */
.rp-section {
  background:#f9f9f9; border:1px solid #e0e0e0; border-radius:10px;
  padding:16px; margin-bottom:10px;
  transition:border-color .2s;
}
.rp-section:hover { border-color:rgba(201,168,76,.3); }
.rp-title {
  font-size:.62rem; font-weight:800; color:#a07830;
  letter-spacing:1.6px; text-transform:uppercase; margin-bottom:8px;
}
.rp-sub { font-size:.76rem; color:#666666; margin-bottom:10px; }

/* ══ BUTTONS ═══════════════════════════════════════════════════════════════ */
[data-testid="stButton"] > button {
  background:#ffffff!important; color:#a07830!important;
  border:1px solid rgba(201,168,76,.4)!important;
  border-radius:7px!important; font-size:.84rem!important;
  font-weight:600!important; letter-spacing:.3px!important;
  transition:all .18s!important;
}
[data-testid="stButton"] > button:hover {
  background:#fdf8ee!important;
  border-color:#c9a84c!important;
  box-shadow:0 0 20px rgba(201,168,76,.15)!important;
  color:#7a5c1e!important;
  transform:translateY(-1px)!important;
}
[data-testid="stButton"] > button[kind="primary"],
[data-testid="stButton"] > button[kind="primaryFormSubmit"] {
  background:linear-gradient(135deg,#a67c00,#c9a84c)!important;
  border:none!important; color:#ffffff!important;
  font-weight:700!important; letter-spacing:.5px!important;
}
[data-testid="stButton"] > button[kind="primary"]:hover,
[data-testid="stButton"] > button[kind="primaryFormSubmit"]:hover {
  background:linear-gradient(135deg,#c9a84c,#e8c547)!important;
  box-shadow:0 4px 22px rgba(201,168,76,.3)!important;
  transform:translateY(-2px)!important;
}

/* ══ INPUTS & SELECTS ══════════════════════════════════════════════════════ */
[data-testid="stTextInput"] input {
  background:#ffffff!important; color:#111111!important;
  border:1px solid #dddddd!important; border-radius:7px!important;
  font-size:.88rem!important; transition:border-color .18s!important;
}
[data-testid="stTextInput"] input:focus {
  border-color:#c9a84c!important;
  box-shadow:0 0 0 2px rgba(201,168,76,.15)!important;
}
[data-testid="stSelectbox"] > div > div {
  background:#ffffff!important; color:#111111!important;
  border-color:#dddddd!important; border-radius:7px!important;
}

/* ══ FILE UPLOADER ═════════════════════════════════════════════════════════ */
[data-testid="stFileUploader"] {
  background:#f9f9f9!important; border-color:#dddddd!important;
  border-radius:8px!important;
}

/* ══ EXPANDER ══════════════════════════════════════════════════════════════ */
[data-testid="stExpander"] {
  background:#f9f9f9!important; border:1px solid #e0e0e0!important;
  border-radius:8px!important; transition:border-color .18s!important;
}
[data-testid="stExpander"]:hover { border-color:rgba(201,168,76,.3)!important; }
[data-testid="stExpander"] summary { color:#a07830!important; font-size:.85rem!important; }

/* ══ TABS ══════════════════════════════════════════════════════════════════ */
[data-baseweb="tab-list"] { background:#f5f5f5!important; border-bottom:1px solid #e0e0e0!important; }
[data-baseweb="tab"] { color:#666666!important; font-size:.85rem!important; transition:color .15s!important; }
[data-baseweb="tab"]:hover { color:#a07830!important; }
[data-baseweb="tab"][aria-selected="true"] {
  color:#a07830!important;
  border-bottom:2px solid #c9a84c!important;
}

/* ══ SCROLLBAR ═════════════════════════════════════════════════════════════ */
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:#f0f0f0; }
::-webkit-scrollbar-thumb { background:#cccccc; border-radius:2px; }
::-webkit-scrollbar-thumb:hover { background:#c9a84c; }

/* ══ STATUS / ALERTS ═══════════════════════════════════════════════════════ */
[data-testid="stAlert"] {
  background:#fdf8ee!important; border-radius:8px!important;
  border-left-color:#c9a84c!important;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_results() -> list[dict]:
    out = []
    for p in sorted(OUTPUT_DIR.glob("*_result.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            d["_path"] = str(p)
            out.append(d)
        except Exception:
            pass
    return out


def prettify(job_id: str) -> str:
    name = re.sub(r"_\d{4}-\d{2}-\d{2}T[\d-]+$", "", job_id)
    return name.replace("_", " ").replace("-", " ").title() or job_id


def parse_date(job_id: str) -> str:
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})T(\d{2})-(\d{2})", job_id)
    if m:
        y, mo, d, h, mi = m.groups()
        return datetime(int(y), int(mo), int(d), int(h), int(mi)).strftime("%a, %b %d · %I:%M %p").replace(" 0", " ")
    return ""


def get_duration(transcript: list) -> str:
    if not transcript:
        return "-"
    last = transcript[-1].get("end", "00:00:00").split(":")
    try:
        mins = int(last[0]) * 60 + int(last[1])
        return f"{mins} min" if mins else "< 1 min"
    except Exception:
        return "-"


def get_chapters(transcript: list, n: int = 4) -> list[dict]:
    segs = [s for s in transcript if len(s.get("text", "")) > 15]
    if not segs:
        return []
    step = max(1, len(segs) // n)
    out = []
    for i in range(0, len(segs), step):
        txt = segs[i]["text"].strip()
        out.append({"time": segs[i]["start"][:5], "title": txt[:60] + ("…" if len(txt) > 60 else "")})
        if len(out) >= n:
            break
    return out


def risk_chip(risks: list) -> str:
    n = len(risks)
    if n == 0:
        return '<span class="risk-ok">✓ No risks</span>'
    if n <= 3:
        return f'<span class="risk-med">⚠ {n} risk{"s" if n>1 else ""}</span>'
    return f'<span class="risk-high">⚠ {n} risks</span>'


def count_minutes(results: list) -> int:
    total = 0
    for r in results:
        t = r.get("transcript", [])
        if t:
            parts = t[-1].get("end", "00:00:00").split(":")
            try:
                total += int(parts[0]) * 60 + int(parts[1])
            except Exception:
                pass
    return total


def server_status() -> dict | None:
    try:
        r = requests.get(f"{FASTAPI_URL}/health", timeout=1)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def get_upcoming() -> list:
    try:
        r = requests.get(f"{FASTAPI_URL}/api/upcoming-meetings", timeout=1)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


# ── Requirements helpers ──────────────────────────────────────────────────────

def _run_req_pipeline(transcript, model: str):
    from app.requirements.extraction import extract_requirements
    from app.requirements.embedding import build_corpus_index
    from app.requirements.scoring import score_requirements
    from app.requirements.reporting import generate_report, save_report
    reqs   = extract_requirements(transcript, model)
    corpus = build_corpus_index(transcript)
    scored = score_requirements(reqs, corpus)
    report = generate_report(transcript, scored, corpus)
    save_report(report, REQ_OUTPUT_DIR)
    return report


def req_from_json(raw: dict, model: str) -> tuple[bool, str]:
    try:
        from app.requirements.ingestion import load_and_validate
        t = load_and_validate(raw)
    except Exception as e:
        return False, f"Invalid transcript: {e}"
    try:
        _run_req_pipeline(t, model)
        return True, t.title
    except Exception as e:
        return False, str(e)


def req_from_audio(file_bytes: bytes, filename: str, model: str) -> tuple[bool, str]:
    try:
        import whisper as _w
    except ImportError:
        return False, "openai-whisper not installed."
    suffix = Path(filename).suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        result = _w.load_model("base").transcribe(tmp_path, verbose=False)
    except Exception as e:
        return False, f"Whisper failed: {e}"
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    segs = result.get("segments", [])
    if not segs:
        return False, "No speech detected in recording."
    raw = {
        "meeting_id": f"upload_{datetime.now().strftime('%Y%m%dT%H%M%S')}",
        "title": Path(filename).stem.replace("_", " ").replace("-", " ").title(),
        "date": datetime.now(timezone.utc).isoformat(),
        "participants": [],
        "turns": [{"speaker": "Speaker", "start_time": float(s["start"]),
                   "end_time": float(s["end"]), "text": s["text"].strip()}
                  for s in segs if s.get("text", "").strip()],
    }
    return req_from_json(raw, model)


@st.cache_data(show_spinner=False)
def list_req_reports() -> list[str]:
    return [p.name for p in sorted(REQ_OUTPUT_DIR.glob("report_*.json"),
                                   key=lambda p: p.stat().st_mtime, reverse=True)]


def load_req_report(name: str) -> dict:
    return json.loads((REQ_OUTPUT_DIR / name).read_text(encoding="utf-8"))


def fmt_t(s: float) -> str:
    m, sec = divmod(int(s), 60)
    return f"{m:02d}:{sec:02d}"


def tier_badge(tier: str) -> str:
    cls = {"verified": "tier-v", "ambiguous": "tier-a", "unverified": "tier-u"}.get(tier, "tier-u")
    icon = {"verified": "✓", "ambiguous": "⚠", "unverified": "✗"}.get(tier, "?")
    return f'<span class="{cls}">{icon} {tier}</span>'


def acc_badge(acc: float) -> str:
    if acc >= 0.85: return '<span class="badge-g">HIGH CONFIDENCE</span>'
    if acc >= 0.60: return '<span class="badge-y">REVIEW NEEDED</span>'
    return '<span class="badge-r">LOW CONFIDENCE</span>'


def reqs_csv(reqs: list) -> str:
    return pd.DataFrame([{"ID": r["id"], "Title": r["title"], "Type": r["type"],
                          "Priority": r["priority"], "Raised By": r["raised_by"],
                          "Score": r["best_score"], "Tier": r["confidence_tier"],
                          "Description": r["description"]} for r in reqs]).to_csv(index=False)


# ── SOP & report generation ───────────────────────────────────────────────────

_SOP_SECTIONS = [
    ("Call Opening",       15, "Professional greeting with name/company · Purpose clearly stated · Agenda or objectives set for the call"),
    ("Needs Discovery",    20, "Client's primary problem or pain point identified · Open-ended discovery questions asked · Understanding confirmed back to client"),
    ("Qualification",      15, "Budget explored or acknowledged · Project timeline discussed · Decision-makers or stakeholders identified"),
    ("Solution Alignment", 20, "Solution matched to the identified problem · Technical platform or requirements discussed · Value proposition clearly communicated"),
    ("Objection Handling", 15, "All objections/concerns acknowledged · Responded with relevant information or evidence · Client satisfaction with response confirmed"),
    ("Call Closing",       15, "Clear next steps defined with owners assigned · Follow-up timeline agreed upon · Call ended on a positive note"),
]



def _generate_pdf_report(rec: dict) -> bytes:
    from fpdf import FPDF

    job_id     = rec.get("job_id", "recording")
    title      = prettify(job_id)
    date_str   = parse_date(job_id)
    transcript = rec.get("transcript", []) or []
    duration   = get_duration(transcript)
    fields     = rec.get("extracted_fields", {}) or {}
    risk       = rec.get("risk_report", {}) or {}
    risks      = risk.get("risks", []) or []
    needs_rev  = risk.get("needs_review", False)
    gen_time   = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    def _s(v):
        if v is None: return "-"
        s = str(v)
        s = (s.replace("—", "-").replace("–", "-")
              .replace("‘", "'").replace("’", "'")
              .replace("“", '"').replace("”", '"')
              .replace("•", "*").replace("…", "...")
              .replace("é", "e").replace("à", "a")
              .replace("ó", "o").replace("ü", "u"))
        return s.encode("latin-1", "replace").decode("latin-1")

    def _conf_color(s):
        if s is None: return (156, 163, 175)
        return (22, 163, 74) if s >= 85 else (217, 119, 6) if s >= 65 else (220, 38, 38)

    def _score_color(s, hi=8, md=6):
        if s is None: return (156, 163, 175)
        return (22, 163, 74) if s >= hi else (217, 119, 6) if s >= md else (220, 38, 38)

    GOLD  = (160, 120, 48)
    DARK  = (31, 41, 55)
    GRAY  = (100, 116, 139)
    LGRAY = (243, 244, 246)
    BORD  = (220, 220, 220)
    GREEN = (22, 163, 74)
    RED   = (220, 38, 38)
    AMBER = (217, 119, 6)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    W = pdf.w - 40

    # ── helpers ──────────────────────────────────────────────────────
    def sec_title(text):
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*GOLD)
        pdf.cell(0, 5, text.upper(), ln=True)
        pdf.set_draw_color(*BORD)
        pdf.set_line_width(0.3)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(5)
        pdf.set_text_color(*DARK)

    def score_card(x, y, cw, big, lbl, sub, color):
        pdf.set_fill_color(249, 249, 249)
        pdf.set_draw_color(*BORD)
        pdf.rect(x, y, cw, 30, style="FD")
        pdf.set_font("Helvetica", "B", 17)
        pdf.set_text_color(*color)
        pdf.set_xy(x, y + 4)
        pdf.cell(cw, 8, big, align="C")
        pdf.set_font("Helvetica", "", 6)
        pdf.set_text_color(*GRAY)
        pdf.set_xy(x, y + 14)
        pdf.cell(cw, 4, lbl.upper(), align="C")
        if sub:
            pdf.set_font("Helvetica", "B", 6.5)
            pdf.set_text_color(*color)
            pdf.set_xy(x, y + 20)
            pdf.cell(cw, 4, sub.upper(), align="C")

    def field_box(label, value, color):
        pdf.set_fill_color(*LGRAY)
        pdf.set_draw_color(*BORD)
        x0 = pdf.get_x(); y0 = pdf.get_y()
        # label
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.set_text_color(*color)
        pdf.cell(0, 5, label.upper(), ln=True)
        # value
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK)
        pdf.multi_cell(W, 5, _s(value) if not isinstance(value, list) else
                       ("\n".join(f"  > {_s(v)}" for v in value if v) or "-"), ln=True)
        pdf.ln(2)

    def two_col_list(left_title, left_color, left_items,
                     right_title, right_color, right_items):
        if not left_items and not right_items: return
        half = (W - 5) / 2
        y0 = pdf.get_y(); x0 = pdf.l_margin
        # left
        pdf.set_fill_color(240, 255, 244); pdf.set_draw_color(187, 247, 208)
        if left_items:
            pdf.rect(x0, y0, half, 6 + len(left_items) * 6, style="FD")
            pdf.set_xy(x0 + 2, y0 + 1)
            pdf.set_font("Helvetica", "B", 6.5)
            pdf.set_text_color(*left_color)
            pdf.cell(half - 4, 4, left_title.upper())
            for i, item in enumerate(left_items):
                pdf.set_xy(x0 + 4, y0 + 6 + i * 6)
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*DARK)
                pdf.cell(half - 6, 5, _s(item)[:70])
        # right
        rx = x0 + half + 5
        pdf.set_fill_color(255, 245, 245); pdf.set_draw_color(254, 202, 202)
        if right_items:
            pdf.rect(rx, y0, half, 6 + len(right_items) * 6, style="FD")
            pdf.set_xy(rx + 2, y0 + 1)
            pdf.set_font("Helvetica", "B", 6.5)
            pdf.set_text_color(*right_color)
            pdf.cell(half - 4, 4, right_title.upper())
            for i, item in enumerate(right_items):
                pdf.set_xy(rx + 4, y0 + 6 + i * 6)
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*DARK)
                pdf.cell(half - 6, 5, _s(item)[:70])
        max_h = max(
            6 + len(left_items) * 6 if left_items else 0,
            6 + len(right_items) * 6 if right_items else 0,
        )
        pdf.set_y(y0 + max_h + 4)

    def numbered_list(items, color):
        for i, item in enumerate(items, 1):
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_text_color(*color)
            pdf.cell(7, 5, str(i) + ".")
            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_text_color(*DARK)
            pdf.multi_cell(W - 7, 5, _s(item), ln=True)
        pdf.ln(1)

    def text_box(text, bg=(249,249,249), border_color=None, left_accent=None):
        if not text: return
        if left_accent:
            pdf.set_fill_color(*bg)
            pdf.set_draw_color(*BORD)
            x0 = pdf.l_margin; y0 = pdf.get_y()
            # measure height
            old_xy = (pdf.get_x(), pdf.get_y())
            lines = pdf.multi_cell(W - 4, 5, _s(text), split_only=True)
            h = max(len(lines) * 5 + 6, 12)
            pdf.set_fill_color(*bg); pdf.rect(x0, y0, W, h, style="F")
            pdf.set_fill_color(*left_accent); pdf.rect(x0, y0, 3, h, style="F")
            pdf.set_draw_color(*BORD); pdf.rect(x0, y0, W, h, style="D")
            pdf.set_xy(x0 + 6, y0 + 3)
            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_text_color(*DARK)
            pdf.multi_cell(W - 8, 5, _s(text), ln=True)
            pdf.set_y(y0 + h + 3)
        else:
            pdf.set_fill_color(*bg)
            pdf.set_draw_color(*BORD)
            x0 = pdf.l_margin; y0 = pdf.get_y()
            lines = pdf.multi_cell(W, 5, _s(text), split_only=True)
            h = max(len(lines) * 5 + 6, 12)
            pdf.rect(x0, y0, W, h, style="FD")
            pdf.set_xy(x0 + 4, y0 + 3)
            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_text_color(*DARK)
            pdf.multi_cell(W - 8, 5, _s(text), ln=True)
            pdf.set_y(y0 + h + 3)

    # ── Page header ──────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 17)
    pdf.set_text_color(*DARK)
    pdf.multi_cell(0, 9, _s(title), ln=True)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 5, _s(f"{date_str or 'Unknown date'}   ·   {duration}   ·   Generated {gen_time}"), ln=True)
    pdf.set_draw_color(*BORD); pdf.set_line_width(0.5)
    pdf.line(pdf.l_margin, pdf.get_y() + 2, pdf.w - pdf.r_margin, pdf.get_y() + 2)
    pdf.ln(8)

    # ── Summary Scores ───────────────────────────────────────────────
    conf_score  = fields.get("conformance_score")
    conf_status = (fields.get("conformance_status") or "").upper()
    call_score  = fields.get("call_score")
    call_rating = (fields.get("call_rating") or "").title()
    ind_score   = fields.get("individual_score")

    sec_title("Summary Scores")
    y0 = pdf.get_y(); gap = 3; cw = (W - gap * 3) / 4; x0 = pdf.l_margin
    conf_disp = f"{int(float(conf_score))}/100" if conf_score is not None else "-"
    score_card(x0,             y0, cw, conf_disp,
               "Conformance", conf_status, _conf_color(conf_score))
    score_card(x0+cw+gap,      y0, cw,
               f"{float(call_score):.1f}/10" if call_score is not None else "-",
               "Call Quality", call_rating, _score_color(call_score))
    score_card(x0+2*(cw+gap),  y0, cw,
               f"{float(ind_score):.1f}/10" if ind_score is not None else "-",
               "Individual", "", _score_color(ind_score))
    score_card(x0+3*(cw+gap),  y0, cw, str(len(risks)),
               "Risk Items", "NEEDS REVIEW" if needs_rev else "CLEAR",
               RED if needs_rev else GREEN)
    pdf.set_y(y0 + 36)

    # ── Meeting Information ──────────────────────────────────────────
    sec_title("Meeting Information")
    half = (W - 5) / 2
    pairs = [
        ("Client / Account", fields.get("client_name"),    "#3b82f6", (59,130,246)),
        ("Client Problem",   fields.get("client_problem"), "#0ea5e9", (14,165,233)),
        ("Timeline",         fields.get("timeline"),       "#8b5cf6", (139,92,246)),
        ("Budget",           fields.get("budget"),         "#22c55e", (34,197,94)),
    ]
    x0 = pdf.l_margin
    for idx, (lbl, val, _, color) in enumerate(pairs):
        col_x = x0 if idx % 2 == 0 else x0 + half + 5
        if idx % 2 == 0 and idx > 0:
            pdf.ln(2)
        y_now = pdf.get_y()
        pdf.set_fill_color(249, 249, 249)
        pdf.set_draw_color(*BORD)
        pdf.set_draw_color(*(int(color[0]), int(color[1]), int(color[2])))
        pdf.set_line_width(0.8)
        pdf.rect(col_x, y_now, half, 18, style="D")
        pdf.set_line_width(0.3)
        pdf.set_fill_color(*(int(color[0]), int(color[1]), int(color[2])))
        pdf.rect(col_x, y_now, 2.5, 18, style="F")
        pdf.set_xy(col_x + 5, y_now + 2)
        pdf.set_font("Helvetica", "B", 6)
        pdf.set_text_color(*(int(color[0]), int(color[1]), int(color[2])))
        pdf.cell(half - 7, 4, lbl.upper())
        pdf.set_xy(col_x + 5, y_now + 7)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*DARK)
        pdf.cell(half - 7, 6, _s(val))
        if idx % 2 == 1:
            pdf.set_y(y_now + 22)
    if len(pairs) % 2 == 1:
        pdf.set_y(pdf.get_y() + 22)
    pdf.ln(2)

    # ── Conformance ──────────────────────────────────────────────────
    conf_passed = fields.get("conformance_passed") or []
    conf_missed = fields.get("conformance_missed") or []
    if conf_score is not None or conf_passed or conf_missed:
        sec_title("Conformance Assessment")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*GRAY)
        pdf.cell(0, 5, f"SOP Score: {conf_disp}  |  Status: {conf_status or '-'}  |  PASS >= 85  REVIEW 65-84  FAIL < 65", ln=True)
        pdf.ln(2)
        two_col_list("Criteria Met", GREEN, conf_passed, "Criteria Missed", RED, conf_missed)

        # SOP table
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.set_text_color(*GOLD)
        pdf.cell(0, 4, "SOP EVALUATION CRITERIA", ln=True)
        pdf.ln(1)
        col_w = [45, 18, W - 63]
        headers = ["Section", "Max Pts", "Criteria"]
        pdf.set_fill_color(243, 244, 246)
        pdf.set_draw_color(*BORD)
        for i, (h, cw2) in enumerate(zip(headers, col_w)):
            pdf.set_font("Helvetica", "B", 6.5)
            pdf.set_text_color(*GRAY)
            pdf.cell(cw2, 5, h, border=1, fill=True, align="C" if i == 1 else "L")
        pdf.ln()
        for name, pts, desc in _SOP_SECTIONS:
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_text_color(*DARK)
            pdf.cell(col_w[0], 6, _s(name), border=1)
            pdf.set_font("Helvetica", "", 7.5)
            pdf.cell(col_w[1], 6, str(pts), border=1, align="C")
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(*GRAY)
            pdf.cell(col_w[2], 6, _s(desc)[:80], border=1)
            pdf.ln()
        pdf.set_text_color(*DARK)

    # ── Assessment of Call ───────────────────────────────────────────
    call_summary    = fields.get("call_summary")
    call_highlights = fields.get("call_highlights") or []
    call_concerns   = fields.get("call_concerns")   or []
    if call_score is not None or call_summary:
        sec_title("Assessment of Call")
        if call_summary:
            text_box(call_summary)
        two_col_list("Highlights", GREEN, call_highlights, "Concerns", RED, call_concerns)

    # ── Assessment of Individual ─────────────────────────────────────
    ind_summary      = fields.get("individual_summary")
    ind_strengths    = fields.get("individual_strengths")    or []
    ind_improvements = fields.get("individual_improvements") or []
    if ind_score is not None or ind_summary:
        sec_title("Assessment of Individual")
        if ind_summary:
            text_box(ind_summary)
        two_col_list("Strengths", GREEN, ind_strengths, "To Improve", AMBER, ind_improvements)

    # ── Insights & Next Actions ──────────────────────────────────────
    call_insights = fields.get("call_insights") or []
    next_steps    = fields.get("next_steps")    or []
    if call_insights or next_steps:
        sec_title("Insights on Call & Next Actions")
        half = (W - 5) / 2
        x0   = pdf.l_margin
        y0   = pdf.get_y()
        # Left: insights
        if call_insights:
            pdf.set_font("Helvetica", "B", 6.5); pdf.set_text_color(*AMBER)
            pdf.set_xy(x0, y0); pdf.cell(half, 4, "KEY INSIGHTS", ln=False)
            for i, ins in enumerate(call_insights, 1):
                pdf.set_xy(x0, pdf.get_y() + (4 if i == 1 else 0))
                pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*AMBER)
                pdf.cell(6, 5, str(i) + ".")
                pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*DARK)
                pdf.multi_cell(half - 6, 5, _s(ins), ln=True)
        # Right: next actions
        if next_steps:
            ry0 = y0; rx = x0 + half + 5
            pdf.set_font("Helvetica", "B", 6.5); pdf.set_text_color(*GREEN)
            pdf.set_xy(rx, ry0); pdf.cell(half, 4, "NEXT ACTIONS", ln=False)
            pdf.set_y(ry0 + 4)
            for i, step in enumerate(next_steps, 1):
                pdf.set_xy(rx, pdf.get_y())
                pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*GREEN)
                pdf.cell(6, 5, str(i) + ".")
                pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*DARK)
                pdf.multi_cell(half - 6, 5, _s(step), ln=True)

    # ── Conclusions ──────────────────────────────────────────────────
    conclusions = fields.get("conclusions")
    if conclusions:
        sec_title("Conclusions")
        text_box(conclusions, bg=(255, 251, 235), left_accent=(201, 168, 76))

    # ── Tech Stack ───────────────────────────────────────────────────
    tech = fields.get("techstack_platform") or []
    if tech:
        sec_title("Tech Stack")
        chips = (tech if isinstance(tech, list) else [tech])
        x0 = pdf.l_margin; y0 = pdf.get_y(); cx = x0
        for t in chips:
            t = _s(t)
            pdf.set_font("Helvetica", "", 8)
            w2 = pdf.get_string_width(t) + 8
            if cx + w2 > pdf.w - pdf.r_margin:
                cx = x0; y0 += 8; pdf.set_y(y0)
            pdf.set_fill_color(254, 249, 238)
            pdf.set_draw_color(201, 168, 76)
            pdf.rect(cx, y0, w2, 6, style="FD")
            pdf.set_xy(cx + 2, y0 + 0.5)
            pdf.set_text_color(*GOLD)
            pdf.cell(w2 - 4, 5, t)
            cx += w2 + 3
        pdf.set_y(y0 + 10)

    # ── Requirements ─────────────────────────────────────────────────
    reqs_list = fields.get("strict_requirements") or []
    if reqs_list:
        sec_title(f"Requirements  ({len(reqs_list)} items)")
        for i, r in enumerate(reqs_list, 1):
            pdf.set_fill_color(254, 249, 238)
            pdf.set_draw_color(201, 168, 76)
            pdf.set_font("Helvetica", "B", 6.5)
            pdf.set_text_color(*GOLD)
            pdf.cell(18, 5, f"REQ {i:02d}", border=1, fill=True)
            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_text_color(*DARK)
            pdf.multi_cell(W - 18, 5, _s(r), border="B", ln=True)

    # ── Risk Report ───────────────────────────────────────────────────
    sec_title("Risk Report")
    if risks:
        for r_item in risks:
            desc = r_item if isinstance(r_item, str) else (r_item.get("description") or r_item.get("text") or str(r_item))
            text_box(desc, bg=(255, 251, 235), left_accent=(201, 168, 76))
    else:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*GREEN)
        pdf.cell(0, 6, "No risks identified in this recording.", ln=True)

    # ── Footer ───────────────────────────────────────────────────────
    pdf.set_y(-20)
    pdf.set_draw_color(*BORD); pdf.set_line_width(0.3)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 6, f"Call Intelligence  ·  AI-Generated Report  ·  {gen_time}", align="C")

    return bytes(pdf.output())




# ── Per-recording dashboard ───────────────────────────────────────────────────

def _field_card(label: str, value, color: str, wide: bool = False) -> str:
    if isinstance(value, list):
        inner = "".join(
            f"<div style='display:flex;gap:8px;align-items:flex-start;padding:4px 0;"
            f"border-bottom:1px solid #e8e8e8'>"
            f"<span style='color:{color};font-weight:700;margin-top:1px'>›</span>"
            f"<span style='font-size:.84rem;color:#1f2937'>{v}</span></div>"
            for v in value if v
        ) if value else "<span style='color:#666666;font-size:.84rem'>—</span>"
    else:
        inner = f"<div style='font-size:.92rem;color:#111111;font-weight:500'>{value or '—'}</div>"
    return (
        f"<div style='background:#f9f9f9;border:1px solid #e0e0e0;border-left:4px solid {color};"
        f"border-radius:10px;padding:14px 16px;margin-bottom:12px'>"
        f"<div style='font-size:.68rem;font-weight:700;color:{color};text-transform:uppercase;"
        f"letter-spacing:.6px;margin-bottom:8px'>{label}</div>"
        f"{inner}</div>"
    )


def _render_recording_dashboard(rec: dict) -> None:
    job_id     = rec.get("job_id", "recording")
    title      = prettify(job_id)
    date_str   = parse_date(job_id)
    transcript = rec.get("transcript", []) or []
    duration   = get_duration(transcript)
    fields     = rec.get("extracted_fields", {}) or {}
    risk       = rec.get("risk_report",     {}) or {}
    risks      = risk.get("risks", []) or []
    needs_rev  = risk.get("needs_review", False)

    # ── back + header + download ───────────────────────────────────────────
    hdr_back, hdr_title, hdr_dl = st.columns([1, 9, 2])
    with hdr_back:
        if st.button("Back", key="back_btn"):
            st.session_state.pop("selected_recording", None)
            st.rerun()
    with hdr_title:
        st.markdown(
            f"<div style='font-size:1.4rem;font-weight:700;color:#111111;margin:8px 0 2px'>{title}</div>"
            f"<div style='font-size:.78rem;color:#666666;letter-spacing:.2px'>{date_str or 'Unknown date'}"
            f"{'  ·  ' + duration if duration not in ('-', '') else ''}</div>",
            unsafe_allow_html=True,
        )
    with hdr_dl:
        st.markdown("<div style='margin-top:6px'></div>", unsafe_allow_html=True)
        st.download_button(
            "Download Report",
            data=_generate_pdf_report(rec),
            file_name=f"{job_id}_report.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="btn_download_report",
        )

    st.markdown("<div style='margin:10px 0 6px'></div>", unsafe_allow_html=True)

    # ── stat row ───────────────────────────────────────────────────────────
    _conf_score_raw = fields.get("conformance_score")
    _conf_pct = f"{float(_conf_score_raw):.1f}%" if _conf_score_raw is not None else "—"
    _conf_color = "#4ade80" if (_conf_score_raw or 0) >= 80 else "#fbbf24" if (_conf_score_raw or 0) >= 60 else "#f87171"
    sc1, sc2, sc3, sc4 = st.columns(4)
    for col, num, lbl, color in [
        (sc1, _conf_pct,   "Conformance",    _conf_color),
        (sc2, duration,    "Duration",        "#6366f1"),
        (sc3, len(risks),  "Risks",           "#ef4444" if risks else "#22c55e"),
        (sc4, "Review" if needs_rev else "✓ Clear", "Status", "#ef4444" if needs_rev else "#22c55e"),
    ]:
        with col:
            st.markdown(
                f"<div class='stat-box'><div class='stat-num' style='color:{color};font-size:1.35rem'>{num}</div>"
                f"<div class='stat-lbl'>{lbl}</div></div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='margin:10px 0 4px'></div>", unsafe_allow_html=True)

    # Re-analyze button — re-runs LLM field extraction on stored transcript
    if st.button("Re-analyze with AI", key="btn_reanalyze"):
        result_path = Path(rec.get("_path", ""))
        if not result_path.exists():
            st.error("Result file not found.")
        else:
            with st.status("Re-analyzing…", expanded=True) as _rs:
                try:
                    from app.services.field_extractor import FieldExtractor
                    from app.services.risk_report_service import RiskReportService
                    st.write("Sending transcript to Groq LLM…")
                    new_fields = FieldExtractor().extract(transcript)
                    st.write(f"Fields extracted: {[k for k,v in new_fields.items() if v]}")
                    new_risk = RiskReportService().generate(new_fields, transcript)
                    data = json.loads(result_path.read_text(encoding="utf-8"))
                    data["extracted_fields"] = new_fields
                    data["risk_report"]      = new_risk
                    result_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                    _rs.update(label="Re-analysis complete", state="complete")
                    st.rerun()
                except Exception as _e:
                    _rs.update(label="Re-analysis failed", state="error")
                    st.error(f"Error: {_e}")

    st.markdown("<div style='margin:10px 0'></div>", unsafe_allow_html=True)

    # ── section: meeting info ──────────────────────────────────────────────
    st.markdown("<div class='sec-label'>Meeting Information</div>", unsafe_allow_html=True)
    mi1, mi2 = st.columns(2)
    with mi1:
        st.markdown(_field_card("Client / Account", fields.get("client_name"), "#3b82f6"), unsafe_allow_html=True)
        st.markdown(_field_card("Timeline", fields.get("timeline"), "#8b5cf6"), unsafe_allow_html=True)
    with mi2:
        st.markdown(_field_card("Client Problem", fields.get("client_problem"), "#0ea5e9"), unsafe_allow_html=True)
        st.markdown(_field_card("Budget", fields.get("budget"), "#22c55e"), unsafe_allow_html=True)

    # ── section: conformance ──────────────────────────────────────────────
    conf_score  = fields.get("conformance_score")
    conf_passed = fields.get("conformance_passed") or []
    conf_missed = fields.get("conformance_missed") or []

    if conf_score is not None or conf_passed or conf_missed:
        st.markdown("<div class='sec-label' style='margin-top:6px'>Conformance</div>", unsafe_allow_html=True)

        # ── passed / missed checklist ──────────────────────────────────────
        if conf_passed or conf_missed:
            ci1, ci2 = st.columns(2)
            if conf_passed:
                with ci1:
                    passed_html = "".join(
                        f"<div style='display:flex;gap:8px;align-items:flex-start;padding:6px 0;border-bottom:1px solid #e8e8e8'>"
                        f"<span style='color:#16a34a;font-weight:700;flex-shrink:0;margin-top:1px'>›</span>"
                        f"<span style='font-size:.84rem;color:#1f2937'>{item}</span></div>"
                        for item in conf_passed if item
                    )
                    st.markdown(
                        f"<div style='background:#f0fff4;border:1px solid #bbf7d0;border-radius:10px;padding:12px 16px;margin-bottom:12px'>"
                        f"<div style='font-size:.6rem;color:#16a34a;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px'>Criteria Met</div>"
                        f"{passed_html}</div>",
                        unsafe_allow_html=True,
                    )
            if conf_missed:
                with ci2:
                    missed_html = "".join(
                        f"<div style='display:flex;gap:8px;align-items:flex-start;padding:6px 0;border-bottom:1px solid #e8e8e8'>"
                        f"<span style='color:#dc2626;font-weight:700;flex-shrink:0;margin-top:1px'>›</span>"
                        f"<span style='font-size:.84rem;color:#1f2937'>{item}</span></div>"
                        for item in conf_missed if item
                    )
                    st.markdown(
                        f"<div style='background:#fff5f5;border:1px solid #fecaca;border-radius:10px;padding:12px 16px;margin-bottom:12px'>"
                        f"<div style='font-size:.6rem;color:#dc2626;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px'>Criteria Missed</div>"
                        f"{missed_html}</div>",
                        unsafe_allow_html=True,
                    )

        # ── SOP criteria table (collapsible) ──────────────────────────────
        with st.expander("View SOP Criteria"):
            sop_rows_html = "".join(
                f"<div style='display:flex;gap:0;border-bottom:1px solid #e8e8e8;padding:8px 0'>"
                f"<div style='width:170px;flex-shrink:0;font-size:.8rem;font-weight:700;color:#a07830'>{name}"
                f"<span style='display:block;font-size:.64rem;color:#666666;font-weight:400;margin-top:2px'>{pts} pts</span></div>"
                f"<div style='font-size:.8rem;color:#444444;line-height:1.5'>{desc}</div></div>"
                for name, pts, desc in _SOP_SECTIONS
            )
            st.markdown(
                f"<div style='background:#f9f9f9;border-radius:8px;padding:10px 14px'>"
                f"<div style='font-size:.65rem;color:#888888;margin-bottom:10px;letter-spacing:.5px'>"
                f"PASS ≥ 85 &nbsp;·&nbsp; REVIEW 65–84 &nbsp;·&nbsp; FAIL &lt; 65 &nbsp;·&nbsp; Total 100 pts</div>"
                f"{sop_rows_html}</div>",
                unsafe_allow_html=True,
            )

    # ── section: assessment of call ────────────────────────────────────────
    call_score     = fields.get("call_score")
    call_rating    = (fields.get("call_rating") or "").lower()
    call_summary   = fields.get("call_summary")
    call_highlights = fields.get("call_highlights") or []
    call_concerns   = fields.get("call_concerns") or []

    if call_score is not None or call_summary:
        st.markdown("<div class='sec-label' style='margin-top:6px'>Assessment of Call</div>", unsafe_allow_html=True)
        rating_color = {"excellent": "#4ade80", "good": "#a3e635", "average": "#fbbf24", "poor": "#f87171"}.get(call_rating, "#c9a84c")
        ac1, ac2 = st.columns([1, 3])
        with ac1:
            st.markdown(
                f"<div style='background:#f9f9f9;border:1px solid #e0e0e0;border-radius:10px;padding:18px;text-align:center'>"
                f"<div style='font-size:2rem;font-weight:800;color:{rating_color}'>{f'{float(call_score):.1f}' if call_score is not None else '—'}<span style='font-size:.9rem;color:#666666'>/10</span></div>"
                f"<div style='font-size:.58rem;color:#666666;text-transform:uppercase;letter-spacing:1px;margin-top:4px'>Call Score</div>"
                f"<div style='margin-top:10px'>"
                f"<span style='color:{rating_color};font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px'>{call_rating or '—'}</span>"
                f"</div></div>",
                unsafe_allow_html=True,
            )
        with ac2:
            if call_summary:
                st.markdown(
                    f"<div style='background:#f9f9f9;border:1px solid #e0e0e0;border-radius:10px;padding:12px 16px;font-size:.88rem;color:#1f2937;margin-bottom:10px'>{call_summary}</div>",
                    unsafe_allow_html=True,
                )
            if call_highlights or call_concerns:
                ah1, ah2 = st.columns(2)
                if call_highlights:
                    with ah1:
                        hl_html = "".join(
                            f"<div style='display:flex;gap:8px;padding:4px 0;border-bottom:1px solid #e8e8e8'>"
                            f"<span style='color:#16a34a;font-size:.8rem'>+</span>"
                            f"<span style='font-size:.83rem;color:#1f2937'>{h}</span></div>"
                            for h in call_highlights if h
                        )
                        st.markdown(
                            f"<div style='background:#f0fff4;border:1px solid #bbf7d0;border-radius:8px;padding:10px 14px'>"
                            f"<div style='font-size:.6rem;color:#16a34a;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>Highlights</div>"
                            f"{hl_html}</div>",
                            unsafe_allow_html=True,
                        )
                if call_concerns:
                    with ah2:
                        cn_html = "".join(
                            f"<div style='display:flex;gap:8px;padding:4px 0;border-bottom:1px solid #e8e8e8'>"
                            f"<span style='color:#dc2626;font-size:.8rem'>−</span>"
                            f"<span style='font-size:.83rem;color:#1f2937'>{c}</span></div>"
                            for c in call_concerns if c
                        )
                        st.markdown(
                            f"<div style='background:#fff5f5;border:1px solid #fecaca;border-radius:8px;padding:10px 14px'>"
                            f"<div style='font-size:.6rem;color:#dc2626;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>Concerns</div>"
                            f"{cn_html}</div>",
                            unsafe_allow_html=True,
                        )

    # ── section: assessment of individual ─────────────────────────────────
    ind_score       = fields.get("individual_score")
    ind_summary     = fields.get("individual_summary")
    ind_strengths   = fields.get("individual_strengths") or []
    ind_improvements = fields.get("individual_improvements") or []

    if ind_score is not None or ind_summary:
        st.markdown("<div class='sec-label' style='margin-top:6px'>Assessment of Individual</div>", unsafe_allow_html=True)
        ind_color = "#4ade80" if (ind_score or 0) >= 8 else "#fbbf24" if (ind_score or 0) >= 6 else "#f87171"
        ia1, ia2 = st.columns([1, 3])
        with ia1:
            st.markdown(
                f"<div style='background:#f9f9f9;border:1px solid #e0e0e0;border-radius:10px;padding:18px;text-align:center'>"
                f"<div style='font-size:2rem;font-weight:800;color:{ind_color}'>{f'{float(ind_score):.1f}' if ind_score is not None else '—'}<span style='font-size:.9rem;color:#666666'>/10</span></div>"
                f"<div style='font-size:.58rem;color:#666666;text-transform:uppercase;letter-spacing:1px;margin-top:4px'>Individual Score</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with ia2:
            if ind_summary:
                st.markdown(
                    f"<div style='background:#f9f9f9;border:1px solid #e0e0e0;border-radius:10px;padding:12px 16px;font-size:.88rem;color:#1f2937;margin-bottom:10px'>{ind_summary}</div>",
                    unsafe_allow_html=True,
                )
            if ind_strengths or ind_improvements:
                is1, is2 = st.columns(2)
                if ind_strengths:
                    with is1:
                        st_html = "".join(
                            f"<div style='display:flex;gap:8px;padding:4px 0;border-bottom:1px solid #e8e8e8'>"
                            f"<span style='color:#16a34a;font-size:.8rem'>›</span>"
                            f"<span style='font-size:.83rem;color:#1f2937'>{s}</span></div>"
                            for s in ind_strengths if s
                        )
                        st.markdown(
                            f"<div style='background:#f0fff4;border:1px solid #bbf7d0;border-radius:8px;padding:10px 14px'>"
                            f"<div style='font-size:.6rem;color:#16a34a;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>Strengths</div>"
                            f"{st_html}</div>",
                            unsafe_allow_html=True,
                        )
                if ind_improvements:
                    with is2:
                        im_html = "".join(
                            f"<div style='display:flex;gap:8px;padding:4px 0;border-bottom:1px solid #e8e8e8'>"
                            f"<span style='color:#a07830;font-size:.8rem'>›</span>"
                            f"<span style='font-size:.83rem;color:#1f2937'>{i}</span></div>"
                            for i in ind_improvements if i
                        )
                        st.markdown(
                            f"<div style='background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:10px 14px'>"
                            f"<div style='font-size:.6rem;color:#a07830;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>To Improve</div>"
                            f"{im_html}</div>",
                            unsafe_allow_html=True,
                        )

    # ── section: insights on call & next actions ───────────────────────────
    call_insights = fields.get("call_insights") or []
    insights_next = fields.get("next_steps") or []

    if call_insights or insights_next:
        st.markdown("<div class='sec-label' style='margin-top:6px'>Insights on Call & Next Actions</div>", unsafe_allow_html=True)
        in1, in2 = st.columns(2)
        if call_insights:
            with in1:
                ins_html = "".join(
                    f"<div style='display:flex;gap:10px;align-items:flex-start;padding:7px 0;border-bottom:1px solid #e8e8e8'>"
                    f"<span style='width:18px;height:18px;border-radius:50%;background:#fef9e7;color:#a07830;"
                    f"font-size:.62rem;font-weight:800;display:flex;align-items:center;justify-content:center;"
                    f"flex-shrink:0;margin-top:1px'>{i}</span>"
                    f"<span style='font-size:.85rem;color:#1f2937;line-height:1.5'>{insight}</span></div>"
                    for i, insight in enumerate(call_insights, 1) if insight
                )
                st.markdown(
                    f"<div style='background:#f9f9f9;border:1px solid #e0e0e0;border-radius:10px;padding:12px 16px'>"
                    f"<div style='font-size:.6rem;color:#a07830;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px'>Key Insights</div>"
                    f"{ins_html}</div>",
                    unsafe_allow_html=True,
                )
        if insights_next:
            with in2:
                na_html = "".join(
                    f"<div style='display:flex;gap:10px;align-items:flex-start;padding:7px 0;border-bottom:1px solid #e8e8e8'>"
                    f"<span style='width:18px;height:18px;border-radius:50%;background:#f0fff4;color:#16a34a;"
                    f"font-size:.62rem;font-weight:800;display:flex;align-items:center;justify-content:center;"
                    f"flex-shrink:0;margin-top:1px'>{i}</span>"
                    f"<span style='font-size:.85rem;color:#1f2937;line-height:1.5'>{step}</span></div>"
                    for i, step in enumerate(insights_next, 1) if step
                )
                st.markdown(
                    f"<div style='background:#f9f9f9;border:1px solid #e0e0e0;border-radius:10px;padding:12px 16px'>"
                    f"<div style='font-size:.6rem;color:#16a34a;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px'>Next Actions</div>"
                    f"{na_html}</div>",
                    unsafe_allow_html=True,
                )

    # ── section: conclusions ───────────────────────────────────────────────
    conclusions = fields.get("conclusions")
    if conclusions:
        st.markdown("<div class='sec-label' style='margin-top:6px'>Conclusions</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='background:#fffbeb;border:1px solid #fde68a;border-left:4px solid #c9a84c;"
            f"border-radius:10px;padding:16px 20px;font-size:.9rem;color:#1f2937;line-height:1.65;"
            f"margin-bottom:16px'>{conclusions}</div>",
            unsafe_allow_html=True,
        )

    # ── section: tech stack ────────────────────────────────────────────────
    tech = fields.get("techstack_platform")
    if tech and (tech if isinstance(tech, str) else any(tech)):
        st.markdown("<div class='sec-label' style='margin-top:6px'>Tech Stack</div>", unsafe_allow_html=True)
        tech_vals = tech if isinstance(tech, list) else [tech]
        chips = "".join(f'<span class="chip">{v}</span>' for v in tech_vals if v)
        st.markdown(
            f"<div style='background:#f9f9f9;border:1px solid #e0e0e0;border-radius:10px;padding:12px 14px;margin-bottom:14px'>{chips or '—'}</div>",
            unsafe_allow_html=True,
        )

    # ── section: requirements ─────────────────────────────────────────────
    reqs_list = fields.get("strict_requirements") or []
    if reqs_list:
        st.markdown(
            f"<div class='sec-label' style='margin-top:6px'>Requirements"
            f"<span style='font-weight:400;margin-left:8px;text-transform:none;letter-spacing:0;font-size:.72rem'>{len(reqs_list)} items</span></div>",
            unsafe_allow_html=True,
        )
        req_html = "".join(
            f"<div style='display:flex;gap:12px;align-items:flex-start;padding:8px 0;border-bottom:1px solid #e8e8e8'>"
            f"<span style='background:#fef9e7;color:#a07830;border-radius:4px;padding:2px 8px;"
            f"font-size:.68rem;font-weight:700;white-space:nowrap;margin-top:2px;letter-spacing:.5px'>REQ {i:02d}</span>"
            f"<span style='font-size:.86rem;color:#1f2937;line-height:1.55'>{r}</span></div>"
            for i, r in enumerate(reqs_list, 1)
        )
        st.markdown(
            f"<div style='background:#f9f9f9;border:1px solid #e0e0e0;border-radius:10px;"
            f"padding:14px 18px;max-height:300px;overflow-y:auto;margin-bottom:16px'>{req_html}</div>",
            unsafe_allow_html=True,
        )

    # ── section: risk report ───────────────────────────────────────────────
    st.markdown("<div class='sec-label' style='margin-top:6px'>Risk Report</div>", unsafe_allow_html=True)
    if risks:
        rc1, rc2 = st.columns([3, 1])
        with rc1:
            for r_item in risks:
                desc = r_item if isinstance(r_item, str) else (r_item.get("description") or r_item.get("text") or str(r_item))
                st.markdown(
                    f"<div style='background:#fffbeb;border:1px solid #fde68a;border-left:3px solid #c9a84c;"
                    f"border-radius:8px;padding:10px 14px;margin-bottom:8px;font-size:.85rem;color:#1f2937'>"
                    f"{desc}</div>",
                    unsafe_allow_html=True,
                )
        with rc2:
            rev_color = "#dc2626" if needs_rev else "#16a34a"
            rev_bg    = "#fff5f5" if needs_rev else "#f0fff4"
            rev_bdr   = "#fecaca" if needs_rev else "#bbf7d0"
            rev_label = "Needs Review" if needs_rev else "Looks Good"
            st.markdown(
                f"<div style='background:{rev_bg};border:1px solid {rev_bdr};border-radius:10px;"
                f"padding:18px 12px;text-align:center'>"
                f"<div style='font-size:.75rem;font-weight:700;color:{rev_color};"
                f"letter-spacing:.6px;text-transform:uppercase'>{rev_label}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            "<div style='background:#f0fff4;border:1px solid #bbf7d0;border-radius:8px;"
            "padding:12px 16px;font-size:.86rem;color:#16a34a;font-weight:500'>No risks identified in this recording.</div>",
            unsafe_allow_html=True,
        )

    # ── section: transcript ────────────────────────────────────────────────
    # st.markdown("<div class='sec-label' style='margin-top:16px'>Transcript</div>", unsafe_allow_html=True)
    #
    # if transcript:
    #     try:
    #         seg_lens = [len(s.get("text","")) for s in transcript]
    #         labels   = [s.get("start","")[:5] for s in transcript]
    #         step     = max(1, len(transcript) // 40)
    #         fig = go.Figure(go.Bar(
    #             x=labels[::step], y=seg_lens[::step],
    #             marker_color="#c9a84c", opacity=0.7,
    #         ))
    #         fig.update_layout(
    #             height=120, margin=dict(t=4, b=4, l=0, r=0),
    #             paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    #             xaxis=dict(showgrid=False, tickfont=dict(size=9, color="#94a3b8"), title=""),
    #             yaxis=dict(showgrid=False, showticklabels=False),
    #             showlegend=False,
    #         )
    #         st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    #     except Exception:
    #         pass
    #
    #     with st.expander(f"View transcript  ·  {len(transcript)} segments"):
    #         for seg in transcript:
    #             st.markdown(
    #                 f"`{seg.get('start','?')[:8]}`&nbsp;&nbsp;{seg.get('text','').strip()}",
    #                 unsafe_allow_html=True,
    #             )
    #         full_text = "\n".join(f"[{s.get('start','')[:8]}] {s.get('text','')}" for s in transcript)
    #         st.download_button("Download transcript (.txt)", full_text,
    #                            file_name=f"{job_id}_transcript.txt", mime="text/plain")


# ── TOP-LEVEL: handle recording upload before any layout ─────────────────────
# File bytes are stored in session_state so they survive reruns.

if "upload_bytes" in st.session_state and st.session_state.get("do_process"):
    st.session_state.do_process = False
    file_bytes = st.session_state.pop("upload_bytes")
    filename   = st.session_state.pop("upload_name")

    with st.status(f"Processing **{filename}**…", expanded=True) as _s:
        try:
            from app.services.audio_extractor import extract_audio
            from app.services.stt_service import STTService
            from app.services.transcript_cleaner import clean_segments
            from app.services.field_extractor import FieldExtractor
            from app.services.risk_report_service import RiskReportService
            from app.services.storage_service import StorageService

            st.write("Saving file…")
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            dest = UPLOAD_DIR / filename
            dest.write_bytes(file_bytes)
            job_name  = dest.stem
            audio_out = AUDIO_DIR / f"{job_name}.wav"

            st.write("Extracting audio…")
            extract_audio(dest, audio_out)

            st.write(f"Transcribing with Whisper ({WHISPER_MODEL_SIZE}) — this may take a moment…")
            stt    = STTService(model_size=WHISPER_MODEL_SIZE).transcribe(audio_out)
            segs   = clean_segments(stt["segments"])
            st.write(f"{len(segs)} segments transcribed")

            st.write("Extracting fields and risks with AI…")
            fields = FieldExtractor().extract(segs)
            risk   = RiskReportService().generate(fields, segs)

            st.write("Saving result…")
            storage = StorageService()
            storage.save_json({"language": stt.get("language"), "segments": segs},
                              OUTPUT_DIR / f"{job_name}_transcript.json")
            storage.save_json({"job_id": job_name, "source_file": str(dest),
                               "audio_file": str(audio_out), "transcript": segs,
                               "speaker_segments": [], "extracted_fields": fields,
                               "risk_report": risk},
                              OUTPUT_DIR / f"{job_name}_result.json")

            _s.update(label="Processing complete", state="complete")
            st.session_state.just_processed    = job_name
            st.session_state.selected_recording = job_name

        except Exception as _e:
            _s.update(label="Processing failed", state="error")
            st.error(f"Error: {_e}")
            st.stop()

    st.rerun()


# ── Sidebar ───────────────────────────────────────────────────────────────────

results   = load_results()
total_min = count_minutes(results)
used_pct  = min(int(total_min / 300 * 100), 100)
status_data = server_status()

with st.sidebar:
    st.markdown("""
    <div style="padding:20px 4px 24px">
      <div style="font-size:1.1rem;font-weight:800;color:#a07830;letter-spacing:-.3px">Call Intelligence</div>
      <div style="font-size:.7rem;color:#666666;margin-top:3px;letter-spacing:.5px;text-transform:uppercase">Meeting Analysis Platform</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("Navigation", [
        "Home",
        "Recordings",
        "Live",
        "Calendar",
        "Requirements",
    ], label_visibility="collapsed")

    st.markdown("<div style='margin:16px 0;border-top:1px solid #e0e0e0'></div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="padding:0 2px">
      <div style="font-size:.62rem;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#666666;margin-bottom:8px">Usage</div>
      <div style="background:#e0e0e0;border-radius:3px;height:4px;overflow:hidden;margin-bottom:5px">
        <div style="width:{used_pct}%;height:100%;background:#c9a84c;border-radius:3px"></div>
      </div>
      <div style="font-size:.7rem;color:#666666">{total_min} / 300 min</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin:14px 0 8px'></div>", unsafe_allow_html=True)

    srv_color = "#22c55e" if status_data else "#ef4444"
    srv_label = f"Server online · Whisper {status_data.get('model','base')}" if status_data else "Server offline"
    st.markdown(
        f"<div style='font-size:.72rem;color:{srv_color};padding:2px 0'>"
        f"<span style='display:inline-block;width:7px;height:7px;border-radius:50%;"
        f"background:{srv_color};margin-right:6px;vertical-align:middle'></span>{srv_label}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
    if st.button("Refresh", use_container_width=True):
        st.rerun()


# ── Layout ────────────────────────────────────────────────────────────────────

# Full-width pages — no right panel, sidebar stays visible
if page == "Live":
    st.components.v1.iframe(
        f"{FASTAPI_URL}/static/live_transcription.html",
        height=720,
        scrolling=True,
    )
    st.stop()

if page in ("Home", "Recordings") and st.session_state.get("selected_recording"):
    sel_rec_id = st.session_state["selected_recording"]
    sel_rec = next((r for r in results if r.get("job_id") == sel_rec_id), None)
    if sel_rec:
        if "just_processed" in st.session_state:
            st.success(f"✅ **{st.session_state.pop('just_processed')}** processed successfully.")
        _render_recording_dashboard(sel_rec)
    else:
        st.session_state.pop("selected_recording", None)
        st.rerun()
    st.stop()

col_main, col_right = st.columns([13, 7], gap="large")

# ══════════════════════════  RIGHT PANEL  ════════════════════════════════════

with col_right:

    # ── Upload recording ─────────────────────────────────────────────────────
    st.markdown('<div class="rp-section">', unsafe_allow_html=True)
    st.markdown('<div class="rp-title">Upload Recording</div>', unsafe_allow_html=True)
    st.markdown('<div class="rp-sub">Supports MP4, MOV, WAV, MP3 and more — transcribed automatically</div>', unsafe_allow_html=True)

    up_file = st.file_uploader("recording", type=SUPPORTED_UPLOAD_EXTS,
                               label_visibility="collapsed", key="up_rec")
    if up_file:
        sz = up_file.size / (1024 * 1024)
        st.caption(f"{up_file.name}  ·  {sz:.1f} MB")
        if st.button("Process Recording", type="primary",
                     use_container_width=True, key="btn_process"):
            st.session_state.upload_bytes = up_file.read()
            st.session_state.upload_name  = up_file.name
            st.session_state.do_process   = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Join a live meeting ──────────────────────────────────────────────────
    st.markdown('<div class="rp-section">', unsafe_allow_html=True)
    st.markdown('<div class="rp-title">Join a Live Meeting</div>', unsafe_allow_html=True)
    st.markdown('<div class="rp-sub">Paste a Zoom, Meet or Teams URL to auto-join</div>', unsafe_allow_html=True)

    meeting_url = st.text_input("url", placeholder="https://meet.google.com/...",
                                label_visibility="collapsed", key="meeting_url")
    if meeting_url:
        try:
            from app.agent.link_extractor import extract_meeting_url
            found = extract_meeting_url(meeting_url)
        except Exception:
            found = None
        if found:
            url, platform = found
            st.success(f"{platform.title()} meeting detected")
            if st.button("Join and Record", type="primary", use_container_width=True):
                st.info("Starting bot — check the terminal.")
        else:
            st.error("Unrecognised URL. Paste a Zoom, Meet or Teams link.")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Upcoming meetings ────────────────────────────────────────────────────
    st.markdown('<div class="rp-section">', unsafe_allow_html=True)
    st.markdown('<div class="rp-title">Upcoming Meetings</div>', unsafe_allow_html=True)

    upcoming = get_upcoming()
    if upcoming:
        for mtg in upcoming[:4]:
            t = mtg.get("start_time", "")[:16].replace("T", " ")
            st.markdown(
                f"<div style='font-size:.82rem;padding:6px 0;border-bottom:1px solid #e8e8e8;color:#1f2937'>"
                f"<b>{mtg.get('title','Meeting')}</b>"
                f"<span style='color:#666666;float:right;font-size:.75rem'>{t}</span></div>",
                unsafe_allow_html=True)
    else:
        google_ok = Path(os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")).exists()
        st.caption("Google Calendar connected" if google_ok else "No upcoming meetings. Connect your calendar to auto-join.")
        c1, c2 = st.columns(2)
        c1.button("Google", use_container_width=True, key="btn_gcal")
        c2.button("Outlook", use_container_width=True, key="btn_out")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Summary stats ────────────────────────────────────────────────────────
    need_review = sum(1 for r in results if r.get("risk_report", {}).get("needs_review"))
    s1, s2, s3 = st.columns(3)
    for col, num, lbl, color in [
        (s1, len(results),  "Recordings", "#3b82f6"),
        (s2, total_min,     "Minutes",    "#6366f1"),
        (s3, need_review,   "Needs Review", "#ef4444"),
    ]:
        with col:
            st.markdown(f"""<div class="stat-box">
              <div class="stat-num" style="color:{color}">{num}</div>
              <div class="stat-lbl">{lbl}</div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════  MAIN PANEL  ════════════════════════════════════

with col_main:

    # ── HOME / RECORDINGS ────────────────────────────────────────────────────
    if page in ("Home", "Recordings"):

        sel_rec_id = st.session_state.get("selected_recording")

        # ── Recording dashboard (detail view) ────────────────────────────────
        if sel_rec_id:
            sel_rec = next((r for r in results if r.get("job_id") == sel_rec_id), None)
            if sel_rec:
                if "just_processed" in st.session_state:
                    st.success(f"✅ **{st.session_state.pop('just_processed')}** processed successfully.")
                _render_recording_dashboard(sel_rec)
            else:
                st.session_state.pop("selected_recording", None)
                st.rerun()

        # ── Recording list ────────────────────────────────────────────────────
        else:
            st.markdown(
                f"<div style='margin-bottom:16px'>"
                f"<span style='font-size:1.4rem;font-weight:700;color:#111111'>Recordings</span>"
                f"<span style='font-size:.78rem;color:#666666;margin-left:10px;font-weight:500'>{len(results)} total</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            if "just_processed" in st.session_state:
                st.success(f"{st.session_state.pop('just_processed')} — processed successfully.")

            if not results:
                with st.container(border=True):
                    st.markdown("""
                    <div style="text-align:center;padding:52px 0">
                      <div style="font-size:1.05rem;font-weight:600;color:#111111">No recordings yet</div>
                      <div style="font-size:.85rem;color:#666666;margin-top:6px">Upload a recording using the panel on the right</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                for rec in results:
                    job_id     = rec.get("job_id", "recording")
                    title      = prettify(job_id)
                    date_str   = parse_date(job_id)
                    transcript = rec.get("transcript", [])
                    duration   = get_duration(transcript)
                    chapters   = get_chapters(transcript)
                    risks      = (rec.get("risk_report") or {}).get("risks", [])
                    fields     = rec.get("extracted_fields") or {}

                    with st.container(border=True):
                        cl, cr = st.columns([8, 2])
                        with cl:
                            st.markdown(f"<div class='card-title'>{title}</div>", unsafe_allow_html=True)
                            st.markdown(
                                f"<div class='card-meta'>{date_str or 'Unknown date'}"
                                f"&nbsp;&nbsp;·&nbsp;&nbsp;{duration}</div>",
                                unsafe_allow_html=True,
                            )
                        with cr:
                            if st.button("Open", key=f"dash_{job_id}"):
                                st.session_state.selected_recording = job_id
                                st.rerun()

    # ── LIVE RECORD — handled above as full-width ─────────────────────────
    elif page == "Live":
        pass

    # ── CALENDAR ─────────────────────────────────────────────────────────────
    elif page == "Calendar":
        st.markdown("<div style='font-size:1.4rem;font-weight:700;color:#111111;margin-bottom:18px'>Calendar Integration</div>", unsafe_allow_html=True)

        google_ok  = Path(os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")).exists()
        outlook_ok = bool(os.getenv("MICROSOFT_CLIENT_ID", ""))

        with st.container(border=True):
            st.markdown("<div class='sec-label'>Connected Calendars</div>", unsafe_allow_html=True)
            for name, desc, ok in [
                ("Google Calendar",    "Auto-joins Zoom, Meet and Teams from Google Calendar", google_ok),
                ("Microsoft Outlook", "Auto-joins Teams meetings from Outlook calendar",    outlook_ok),
            ]:
                c1, c2 = st.columns([5, 2])
                c1.markdown(f"**{name}**  \n<span style='font-size:.78rem;color:#666666'>{desc}</span>", unsafe_allow_html=True)
                tag = ("chip chip-green", "Connected") if ok else ("chip", "Not connected")
                c2.markdown(f"<div style='padding-top:27px'><span class='{tag[0]}'>{tag[1]}</span></div>", unsafe_allow_html=True)
                st.markdown("<hr style='border:none;border-top:1px solid #e0e0e0;margin:8px 0'>", unsafe_allow_html=True)

        with st.expander("How to connect Google Calendar"):
            st.markdown("""
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → enable **Google Calendar API**
3. Create **OAuth 2.0 credentials** (Desktop app) → download as `credentials.json`
4. Place `credentials.json` in the project root
5. Set `ENABLE_GOOGLE_CALENDAR=true` in `.env`
6. Run `python -m app.main_agent` — browser opens for OAuth consent on first run
""")
        with st.expander("How to connect Microsoft Outlook / Teams"):
            st.markdown("""
1. Go to [portal.azure.com](https://portal.azure.com) → **App registrations** → New
2. Add delegated permission: **Calendars.Read** (Microsoft Graph)
3. Set in `.env`:
```
ENABLE_OUTLOOK_CALENDAR=true
MICROSOFT_CLIENT_ID=<your-client-id>
MICROSOFT_TENANT_ID=common
```
4. Run `python -m app.main_agent` — device-code login appears once
""")

    # ── REQUIREMENTS ─────────────────────────────────────────────────────────
    elif page == "Requirements":
        st.markdown("<div style='font-size:1.4rem;font-weight:700;color:#111111;margin-bottom:4px'>Requirements Extraction</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:.84rem;color:#666666;margin-bottom:18px'>Upload a recording or transcript — AI extracts and verifies every requirement</div>", unsafe_allow_html=True)

        req_model = st.selectbox("LLM Model", REQ_MODELS, key="req_model")

        up1, up2 = st.columns(2)
        with up1:
            with st.container(border=True):
                st.markdown("**Meeting Recording**")
                st.caption("Whisper transcribes the audio, then requirements are extracted")
                ra = st.file_uploader("rec", type=SUPPORTED_UPLOAD_EXTS, key="req_audio", label_visibility="collapsed")
                if ra:
                    st.caption(f"{ra.name} · {ra.size/(1024*1024):.1f} MB")
                    if st.button("Transcribe and Extract", use_container_width=True, key="btn_ra"):
                        with st.status("Processing…", expanded=True) as _s:
                            st.write("Transcribing with Whisper…")
                            ok, msg = req_from_audio(ra.read(), ra.name, req_model)
                            _s.update(label="Done — " + msg if ok else "Failed", state="complete" if ok else "error")
                            if ok:
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(msg)

        with up2:
            with st.container(border=True):
                st.markdown("**JSON Transcript**")
                st.caption("Upload a transcript JSON in the pipeline format")
                rj = st.file_uploader("json", type=["json"], key="req_json", label_visibility="collapsed")
                if rj:
                    st.caption(f"{rj.name} · {rj.size/1024:.0f} KB")
                    if st.button("Extract Requirements", use_container_width=True, key="btn_rj"):
                        try:
                            raw = json.loads(rj.read())
                        except Exception as e:
                            st.error(f"Invalid JSON: {e}")
                            raw = None
                        if raw:
                            with st.status("Extracting…", expanded=True) as _s:
                                st.write("Calling LLM…")
                                ok, msg = req_from_json(raw, req_model)
                                _s.update(label="Done — " + msg if ok else "Failed", state="complete" if ok else "error")
                                if ok:
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error(msg)

        st.markdown("---")

        rep_names = list_req_reports()
        if not rep_names:
            st.info("No reports yet. Upload a recording or transcript above.")
        else:
            sc, rc = st.columns([5, 1])
            with sc:
                sel = st.selectbox("Report", rep_names, label_visibility="collapsed")
            with rc:
                if st.button("Refresh", use_container_width=True, key="rq_ref"):
                    st.cache_data.clear(); st.rerun()

            rpt     = load_req_report(sel)
            rm, rme = rpt["meta"], rpt["metrics"]
            rqs     = rpt["requirements"]
            rn      = len(rqs)

            # header
            hc1, hc2 = st.columns([4,1])
            with hc1:
                st.markdown(f"**{rm['title']}**  \n<span style='font-size:.8rem;color:#666666'>{rm['date']} · {rm['total_turns']} turns</span>", unsafe_allow_html=True)
            with hc2:
                st.markdown(acc_badge(rme["overall_accuracy"]), unsafe_allow_html=True)
                st.caption(f"Accuracy: {rme['overall_accuracy']:.1%}")

            # metric cards
            mc1,mc2,mc3,mc4 = st.columns(4)
            for col, n2, lbl, color in [
                (mc1, rn, "Total", "#3b82f6"),
                (mc2, rme["verified_count"],   "Verified",   "#15803d"),
                (mc3, rme["ambiguous_count"],  "Ambiguous",  "#a16207"),
                (mc4, rme["unverified_count"], "Unverified", "#b91c1c"),
            ]:
                with col:
                    st.markdown(f"""<div class="stat-box">
                      <div class="stat-num" style="color:{color}">{n2}</div>
                      <div class="stat-lbl">{lbl}</div>
                    </div>""", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            # charts
            cc1,cc2,cc3 = st.columns(3)
            with cc1:
                fig = go.Figure(go.Pie(
                    labels=["Verified","Ambiguous","Unverified"],
                    values=[rme["verified_count"],rme["ambiguous_count"],rme["unverified_count"]],
                    hole=0.55, marker_colors=["#22c55e","#eab308","#ef4444"],
                    textinfo="percent+label", textfont_size=11,
                ))
                fig.update_layout(title="By Confidence", showlegend=False,
                                  margin=dict(t=40,b=5,l=5,r=5), height=230,
                                  paper_bgcolor="rgba(0,0,0,0)",
                                  title_font_color="#a07830")
                st.plotly_chart(fig, use_container_width=True)
            with cc2:
                td = rme.get("by_type",{})
                fig2 = go.Figure(go.Bar(
                    y=[k.replace("_"," ").title() for k in td], x=list(td.values()),
                    orientation="h", marker_color="#c9a84c", text=list(td.values()), textposition="outside",
                    textfont_color="#374151"))
                fig2.update_layout(title="By Type", height=230, margin=dict(t=40,b=5,l=5,r=5),
                                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                   title_font_color="#a07830",
                                   yaxis=dict(tickfont_color="#374151"),
                                   xaxis=dict(tickfont_color="#666666"))
                st.plotly_chart(fig2, use_container_width=True)
            with cc3:
                pd2 = rme.get("by_priority",{})
                pcol = {"must_have":"#f87171","should_have":"#fbbf24","nice_to_have":"#4ade80"}
                fig3 = go.Figure(go.Bar(
                    y=[k.replace("_"," ").title() for k in pd2], x=list(pd2.values()),
                    orientation="h", marker_color=[pcol.get(k,"#aaaaaa") for k in pd2],
                    text=list(pd2.values()), textposition="outside", textfont_color="#374151"))
                fig3.update_layout(title="By Priority", height=230, margin=dict(t=40,b=5,l=5,r=5),
                                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                   title_font_color="#a07830",
                                   yaxis=dict(tickfont_color="#374151"),
                                   xaxis=dict(tickfont_color="#666666"))
                st.plotly_chart(fig3, use_container_width=True)

            # requirements table
            st.markdown("#### Requirements")
            f1,f2,f3,f4 = st.columns([2,2,2,3])
            at = ["verified","ambiguous","unverified"]
            atp= sorted({r["type"] for r in rqs})
            ap = ["must_have","should_have","nice_to_have"]
            with f1: ft = st.multiselect("Tier", at, default=at, placeholder="Tier…", label_visibility="collapsed")
            with f2: ftp= st.multiselect("Type", atp, default=atp, placeholder="Type…", label_visibility="collapsed")
            with f3: fp = st.multiselect("Pri",  ap,  default=ap,  placeholder="Priority…", label_visibility="collapsed")
            with f4: fs = st.text_input("", placeholder="Search title or description…", label_visibility="collapsed")

            filt = [r for r in rqs
                    if r["confidence_tier"] in (ft or at)
                    and r["type"] in (ftp or atp)
                    and r["priority"] in (fp or ap)
                    and (not fs or fs.lower() in r["title"].lower() or fs.lower() in r["description"].lower())]

            st.caption(f"Showing {len(filt)} of {rn}")
            for rq in filt:
                with st.container(border=True):
                    rc1,rc2,rc3,rc4,rc5 = st.columns([1,4,2,2,1.5])
                    rc1.markdown(f"<span style='font-size:.75rem;color:#666666'>{rq['id']}</span>", unsafe_allow_html=True)
                    rc2.markdown(f"**{rq['title']}**")
                    rc3.caption(rq["type"].replace("_"," "))
                    rc4.caption(rq["priority"].replace("_"," "))
                    rc5.markdown(tier_badge(rq["confidence_tier"]), unsafe_allow_html=True)
                    with st.expander("Details"):
                        st.markdown(f"**Description:** {rq['description']}")
                        st.markdown(f"**Score:** `{rq['best_score']:.3f}` &nbsp; **Keywords:** {', '.join(rq.get('keywords',[]))}", unsafe_allow_html=True)
                        st.markdown(f"> *{rq['best_chunk']}*  \n`@ {fmt_t(rq['best_timestamp'])}`")

            st.markdown("---")
            e1,e2,e3 = st.columns(3)
            e1.download_button("Download JSON", json.dumps(rpt,indent=2), f"report_{rm['meeting_id']}.json", "application/json", use_container_width=True)
            e2.download_button("Download CSV",  reqs_csv(rqs), f"reqs_{rm['meeting_id']}.csv", "text/csv", use_container_width=True)
            e3.download_button("Download MD",   f"# {rm['title']}\n\n" + "\n".join(f"- {r['id']}: {r['title']}" for r in rqs if r['priority']=='must_have'),
                               f"summary_{rm['meeting_id']}.md", "text/markdown", use_container_width=True)
