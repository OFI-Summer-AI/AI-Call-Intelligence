import json
import os
import re
from typing import Dict, List

from app.logger import get_logger

logger = get_logger(__name__)

_PROMPT = """You are analyzing a sales/customer meeting transcript.
Return ONLY a valid JSON object — no markdown, no explanation, just the JSON.

Keys required:
- "client_name": string or null
- "client_problem": string or null (1-2 sentence summary of the business problem)
- "strict_requirements": list of strings (up to 8, each under 15 words)
- "techstack_platform": list of strings (specific tools/platforms mentioned)
- "timeline": string or null
- "budget": string or null
- "next_steps": list of strings (up to 6 actionable next steps, each under 20 words)
Use this SOP to evaluate conformance (100 pts total):
  1. Call Opening (15 pts) — Professional greeting with name/company; purpose stated; agenda set
  2. Needs Discovery (20 pts) — Client's primary problem identified; open-ended questions asked; understanding confirmed back to client
  3. Qualification (15 pts) — Budget explored or acknowledged; project timeline discussed; decision-makers or stakeholders identified
  4. Solution Alignment (20 pts) — Solution matched to the identified problem; technical platform or requirements discussed; value proposition clearly communicated
  5. Objection Handling (15 pts) — All objections/concerns acknowledged; responded with relevant information or evidence; client satisfaction with response confirmed
  6. Call Closing (15 pts) — Clear next steps defined with owners; follow-up timeline agreed; call ended on a positive note
  Score thresholds: 85-100 = pass, 65-84 = review, 0-64 = fail
  Map conformance_passed and conformance_missed to specific SOP section names above.

- "conformance_score": integer 0-100 (total score across the 6 SOP sections)
- "conformance_status": one of "pass" (85+), "review" (65-84), "fail" (<65)
- "conformance_passed": list of strings — SOP section names that were satisfactorily met (e.g. "Call Opening", "Needs Discovery")
- "conformance_missed": list of strings — SOP section names that were missed or incomplete (e.g. "Qualification", "Objection Handling")
- "call_score": float 0.0-10.0 with one decimal place (e.g. 7.3)
- "call_rating": one of "excellent", "good", "average", "poor"
- "call_summary": string (2-3 sentence assessment of overall call quality)
- "call_highlights": list of strings (up to 3 positive moments or strengths of the call)
- "call_concerns": list of strings (up to 3 concerns or missed opportunities)
- "individual_score": float 0.0-10.0 with one decimal place (e.g. 8.1)
- "individual_summary": string (1-2 sentence assessment of the individual's performance)
- "individual_strengths": list of strings (up to 3 strengths)
- "individual_improvements": list of strings (up to 3 areas to improve)
- "call_insights": list of strings (up to 4 key insights or observations from the call)
- "conclusions": string (1-2 sentence conclusion on call outcomes and overall status)
- "speaker_scores": list of objects — one per distinguishable speaker (typically 2-4). If speakers are not labelled, infer role from context (e.g. "Sales Rep", "Client"). Each object has these keys: name (string), role (string or null, e.g. sales_rep/client/manager), talk_time_pct (integer 0-100), score (float 0.0-10.0), summary (string, 1 sentence), strengths (list of up to 2 strings), improvements (list of up to 2 strings).

Important: summarize and rewrite in plain English. Do NOT copy raw transcript sentences.

Transcript:
{transcript}
"""

_EMPTY = {
    "client_name": None, "client_problem": None,
    "strict_requirements": [], "techstack_platform": [],
    "timeline": None, "budget": None, "next_steps": [],
    "conformance_score": None, "conformance_status": None,
    "conformance_passed": [], "conformance_missed": [],
    "call_score": None, "call_rating": None,
    "call_summary": None, "call_highlights": [], "call_concerns": [],
    "individual_score": None, "individual_summary": None,
    "individual_strengths": [], "individual_improvements": [],
    "call_insights": [], "conclusions": None,
    "speaker_scores": [],
}


class FieldExtractor:

    def extract(self, transcript_segments: List[Dict]) -> dict:
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            logger.error("OPENAI_API_KEY not set — skipping LLM field extraction")
            return dict(_EMPTY)

        full_text = " ".join(seg.get("text", "") for seg in transcript_segments)
        if not full_text.strip():
            logger.warning("Empty transcript — skipping field extraction")
            return dict(_EMPTY)

        model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        prompt = _PROMPT.format(transcript=full_text[:8000])

        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1800,
            )
            raw = response.choices[0].message.content.strip()
            logger.info("OpenAI raw response (first 300): %s", raw[:300])

            # strip markdown code fences if present
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                fields = json.loads(m.group())
                logger.info("LLM field extraction succeeded: %s", list(fields.keys()))
                return fields

            logger.warning("No JSON object found in LLM response: %s", raw[:300])
        except Exception as exc:
            logger.error("LLM field extraction failed: %s", exc)

        return dict(_EMPTY)
