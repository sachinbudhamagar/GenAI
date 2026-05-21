"""
services/resume_generator.py — LLM-powered resume & cover letter generation.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage

from .llm import get_llm

_SYSTEM_PROMPT = "You are an expert career assistant specialising in resume optimisation."

_USER_PROMPT_TEMPLATE = """
You are a career assistant. Given a resume and a job description, do the following:

1. Rewrite the resume to best match the job description (preserve facts; improve alignment).
2. Write a professional, tailored cover letter using resume details.
3. Provide a brief profile summary (3-4 sentences).
4. Calculate the keyword match % between resume and job description.
5. List important keywords present in the JD but missing from the resume.

Respond using EXACTLY this format — no extra text outside the tags:

<RESUME>
[Rewritten resume]
</RESUME>

<COVERLETTER>
[Cover letter]
</COVERLETTER>

<JSON>
{{
  "JD Match": "X%",
  "MissingKeywords": ["keyword1", "keyword2"]
}}
</JSON>

--- Resume ---
{resume}

--- Job Description ---
{job_description}
"""

_JD_MATCH_PATTERN = re.compile(r"^\d{1,3}%$")


@dataclass
class GenerationResult:
    optimized_resume: str
    cover_letter: str
    jd_match: str
    missing_keywords: list[str]


def generate_resume_and_coverletter(
    resume_text: str,
    job_description: str,
) -> GenerationResult:
    """Generate an optimised resume and cover letter using the LLM.

    Raises:
        EnvironmentError: When no OpenAI key is configured.
        RuntimeError: When the LLM response cannot be parsed.
    """
    llm = get_llm()
    if llm is None:
        raise EnvironmentError(
            "OpenAI API key is missing. Add OPENAI_API_KEY to your .env file."
        )

    prompt = _USER_PROMPT_TEMPLATE.format(
        resume=resume_text,
        job_description=job_description,
    )
    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]
    result = llm.invoke(messages)
    raw = result.content

    optimized_resume = _extract_tag(raw, "RESUME") or "No resume content found."
    cover_letter = _extract_tag(raw, "COVERLETTER") or "No cover letter content found."
    analysis = _extract_analysis(raw)

    return GenerationResult(
        optimized_resume=optimized_resume,
        cover_letter=cover_letter,
        jd_match=analysis.get("JD Match", "N/A"),
        missing_keywords=analysis.get("MissingKeywords", []),
    )


# ── private helpers ──────────────────────────────────────────────────────────

def _extract_tag(text: str, tag: str) -> str:
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_analysis(text: str) -> dict:
    match = re.search(r"<JSON>(.*?)</JSON>", text, re.DOTALL)
    if not match:
        return {}
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}

    jd_match = data.get("JD Match", "")
    if not _JD_MATCH_PATTERN.match(str(jd_match).strip()):
        # Hallucination guard: discard unreliable values
        data["JD Match"] = "N/A"
        data["MissingKeywords"] = []

    return data
