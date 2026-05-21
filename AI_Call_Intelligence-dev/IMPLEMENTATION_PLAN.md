# AI_Call_refactor — Implementation Plan

## Goal
Build a clean, working app in `AI_Call_refactor/` that:
- Uses the **backend logic** from `AI_Call_Intelligence_copy` (richer pipeline: 8 stages, call assessment, conformance scoring, polished transcript, meeting intel, discovery checklist)
- Uses the **frontend design** from `AI_Call_Intelligence-dev` (React + Tailwind + gold theme, FastAPI backend, `railway.toml` + `vercel.json` deployment)
- Fixes all known broken parts from the dev version

---

## What each source contributes

### From `AI_Call_Intelligence_copy` (backend logic)
| Module | What we take |
|--------|-------------|
| `app/services/field_extractor.py` | Full LLM extraction prompt + fallback |
| `app/services/call_assessment_report_service.py` | Polished transcript + conformance + call quality report (complex LLM) |
| `app/services/risk_report_service.py` | Rule-based risk flagging |
| `app/services/meeting_intel_service.py` | Executive summary + speaker role mapping |
| `app/services/call_evaluation_template.py` | 8-question discovery checklist |
| `app/services/storage_service.py` | Atomic JSON writes |
| `app/services/pipeline_artifacts.py` | JobArtifactPaths + polished_to_markdown |
| `app/orchestrator/pipeline.py` | Full 8-stage pipeline with resume logic |
| `app/core/config.py` | Rich config (all env vars, all artifact dirs) |
| `app/services/audio_extractor.py` | FFmpeg WAV extraction |
| `app/services/stt_service.py` | Whisper STT |
| `app/services/openai_diarized_stt_service.py` | OpenAI diarized STT |
| `app/services/transcript_cleaner.py` | Segment cleanup |
| `app/services/speaker_mapper.py` | Speaker overlap assignment |
| `app/services/diarization_service.py` (optional) | pyannote |
| `app/orchestrator/diarization.py` | has_usable_diarization |
| `app/services/video_metadata.py` | ffprobe metadata |
| `app/utils/log.py` | Logging helpers |

### From `AI_Call_Intelligence-dev` (frontend design + API structure)
| Module | What we take |
|--------|-------------|
| `app/static/app.jsx` | Complete React UI (sidebar, all tabs, all components) |
| `app/static/index.html` | HTML shell + CSS + gold theme |
| `app/static/live_transcription.html` | Live transcription standalone page |
| `app/static/*.min.js` | React, ReactDOM, PropTypes, Recharts, Tailwind CDN bundles |
| `app/realtime_server.py` | FastAPI server structure (routes, websocket, static serving) |
| `app/api/routes.py` | Agent lifecycle, calendar, join-now, watcher endpoints |
| `app/services/pipeline_runner.py` | Async pipeline wrapper |
| `app/services/realtime_stt_service.py` | WebSocket live STT |
| `app/agent/` | meeting_bot, scheduler, calendar_watcher, link_extractor, auto_leave |
| `Dockerfile` | CPU-only torch install + ffmpeg |
| `railway.toml` / `vercel.json` | Deployment config |

---

## Key fixes over `AI_Call_Intelligence-dev`

1. **Pipeline**: Replace the 6-step pipeline with the full 8-stage pipeline from `_copy` (adds: meeting intel, call assessment, polished transcript, conformance score, discovery checklist)
2. **API `/api/recordings`**: Return final reports from `data/reports/final/` (schema v3) not just `data/outputs/*_result.json`. Fall back to outputs for compatibility.
3. **API `/api/recordings/{id}/reanalyze`**: Re-run the full assessment (not just field extraction) using the stored transcript.
4. **Frontend data mapping**: The React UI reads `rec.extracted_fields` for scores. The new pipeline stores scores inside `rec.call_quality_report.conformance_score_0_100`. We add a thin adapter layer in the API response so the frontend works unchanged.
5. **`window.__API_BASE__`**: Make it dynamically set via `__RAILWAY_URL__` placeholder (already in `vercel.json`) instead of hardcoded.
6. **PDF generation**: Use the richer report data (polished transcript, conformance, checklist) not just extracted fields.
7. **`/api/process` background task**: Use the new `Pipeline` class (not the old inline 6-step function).
8. **Config**: Merge both configs — use copy's rich path layout but keep dev's `/tmp/app_data` default for Railway/Docker.

---

## Frontend ↔ Backend data contract (adapter)

The React UI reads these fields from each recording object:
```
rec.job_id
rec.transcript           → array of {start, end, text, speaker}
rec.extracted_fields     → {client_name, client_problem, timeline, budget,
                             strict_requirements, techstack_platform,
                             conformance_score, conformance_status,
                             call_score, call_rating, individual_score,
                             call_summary, call_highlights, call_concerns,
                             call_insights, next_steps, conclusions,
                             conformance_passed, conformance_missed,
                             speaker_scores}
rec.risk_report          → {risks: [], needs_review: bool}
```

The new pipeline stores richer data in `call_quality_report`. We add an `_enrich_for_frontend()` function in the API layer that copies relevant fields from `call_quality_report` into `extracted_fields` before returning to the frontend.

Mapping:
```
extracted_fields.conformance_score    ← call_quality_report.conformance_score_0_100
extracted_fields.conformance_status   ← derived from score (pass/review/fail)
extracted_fields.call_score           ← not in new pipeline (leave null)
extracted_fields.call_summary         ← call_quality_report.call_level_summary
extracted_fields.call_insights        ← call_quality_report.insights
extracted_fields.next_steps           ← extracted_fields.next_steps (already there)
extracted_fields.conclusions          ← call_quality_report.conclusion
```

---

## File structure of `AI_Call_refactor/`

```
AI_Call_refactor/
├── run.py                          # Entry: uvicorn app.server:app
├── requirements.txt                # Merged deps (copy's ML + dev's FastAPI/agent)
├── Dockerfile                      # From dev (CPU torch + ffmpeg + playwright)
├── railway.toml                    # Points to AI_Call_refactor/Dockerfile
├── vercel.json                     # Points to AI_Call_refactor/app/static
├── .env.example                    # All env vars documented
│
├── app/
│   ├── __init__.py
│   ├── config.py                   # Merged config (copy's paths + dev's /tmp defaults)
│   ├── logger.py                   # From dev (get_logger)
│   ├── server.py                   # FastAPI app (from dev's realtime_server.py, updated)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py               # From dev (agent/calendar/join-now endpoints)
│   │   └── recordings.py           # NEW: all /api/recordings endpoints (richer data)
│   │
│   ├── pipeline/
│   │   ├── __init__.py
│   │   └── pipeline.py             # From copy's orchestrator/pipeline.py (full 8-stage)
│   │
│   ├── orchestrator/               # Supporting pipeline modules
│   │   ├── __init__.py
│   │   └── diarization.py          # From copy
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── audio_extractor.py      # From copy
│   │   ├── stt_service.py          # From copy
│   │   ├── openai_diarized_stt_service.py  # From copy
│   │   ├── realtime_stt_service.py # From dev (WebSocket live STT)
│   │   ├── transcript_cleaner.py   # From copy
│   │   ├── speaker_mapper.py       # From copy
│   │   ├── field_extractor.py      # From copy (richer LLM extraction)
│   │   ├── risk_report_service.py  # From copy
│   │   ├── call_assessment_report_service.py  # From copy (full assessment)
│   │   ├── meeting_intel_service.py  # From copy
│   │   ├── call_evaluation_template.py  # From copy (8-question checklist)
│   │   ├── storage_service.py      # From copy (atomic writes)
│   │   ├── pipeline_artifacts.py   # From copy (JobArtifactPaths)
│   │   ├── pipeline_runner.py      # From dev (async wrapper)
│   │   ├── video_metadata.py       # From copy
│   │   └── diarization_service.py  # From dev (pyannote, optional)
│   │
│   ├── agent/                      # From dev (calendar bot features)
│   │   ├── __init__.py
│   │   ├── meeting_bot.py
│   │   ├── scheduler.py
│   │   ├── calendar_watcher.py
│   │   ├── link_extractor.py
│   │   └── auto_leave.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   └── log.py                  # From copy (log_stage, configure_logging)
│   │
│   └── static/                     # From dev (React UI, unchanged)
│       ├── index.html              # MODIFIED: __API_BASE__ uses __RAILWAY_URL__ placeholder
│       ├── app.jsx                 # Source (unchanged)
│       ├── app.js                  # Compiled (unchanged)
│       ├── live_transcription.html
│       ├── react.min.js
│       ├── react-dom.min.js
│       ├── prop-types.min.js
│       ├── recharts.js
│       └── tailwind.js
│
└── main_agent.py                   # From dev (agent entry point)
```

---

## Task Checklist

### Phase 1 — Scaffold
- [ ] Create directory structure
- [ ] Copy all static frontend files verbatim
- [ ] Copy all agent/ files verbatim

### Phase 2 — Backend services (from copy)
- [ ] config.py (merged)
- [ ] logger.py
- [ ] utils/log.py
- [ ] services/storage_service.py
- [ ] services/pipeline_artifacts.py
- [ ] services/audio_extractor.py
- [ ] services/stt_service.py
- [ ] services/openai_diarized_stt_service.py
- [ ] services/transcript_cleaner.py
- [ ] services/speaker_mapper.py
- [ ] services/field_extractor.py
- [ ] services/risk_report_service.py
- [ ] services/call_assessment_report_service.py
- [ ] services/meeting_intel_service.py
- [ ] services/call_evaluation_template.py
- [ ] services/video_metadata.py
- [ ] services/diarization_service.py
- [ ] services/realtime_stt_service.py (from dev)
- [ ] services/pipeline_runner.py (from dev)
- [ ] orchestrator/diarization.py
- [ ] pipeline/pipeline.py (full 8-stage from copy)

### Phase 3 — API layer
- [ ] api/routes.py (from dev — agent/calendar endpoints)
- [ ] api/recordings.py (NEW — richer recordings + adapter)
- [ ] server.py (merged FastAPI app)

### Phase 4 — Entry points & deployment
- [ ] run.py
- [ ] main_agent.py
- [ ] requirements.txt
- [ ] Dockerfile
- [ ] railway.toml
- [ ] vercel.json
- [ ] .env.example

### Phase 5 — Frontend fix
- [ ] index.html: fix __API_BASE__ to use placeholder correctly
