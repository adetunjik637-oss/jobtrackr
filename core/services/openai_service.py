"""Generate a tailored cover letter with the OpenAI API."""
from django.conf import settings


class CoverLetterError(Exception):
    pass


TONE_GUIDANCE = {
    "formal": "Use a professional, formal tone. Be respectful and measured.",
    "enthusiastic": "Use a warm, enthusiastic tone that conveys genuine excitement, while staying professional.",
    "concise": "Be concise and direct. Keep it short — three tight paragraphs at most.",
}

SYSTEM_PROMPT = (
    "You are an expert career coach who writes compelling, tailored cover letters. "
    "You write in the first person as the applicant. You never invent facts, "
    "qualifications, or experiences that are not supported by the resume. "
    "You produce a ready-to-send letter with no placeholders, no bracketed "
    "instructions, and no commentary — just the letter itself."
)


def _truncate(text, limit):
    text = (text or "").strip()
    return text[:limit]


def build_prompt(resume_text, job_title, company_name, job_description, tone):
    tone_line = TONE_GUIDANCE.get(tone, TONE_GUIDANCE["formal"])
    return f"""Write a cover letter for the following application.

ROLE: {job_title or "the role"}
COMPANY: {company_name or "the company"}

JOB DESCRIPTION:
{_truncate(job_description, 4000) or "(not provided)"}

APPLICANT'S RESUME:
{_truncate(resume_text, 6000) or "(not provided)"}

INSTRUCTIONS:
- {tone_line}
- Open with a strong hook tied to this specific role and company.
- Draw concrete, relevant points from the resume that match the job.
- Do not fabricate experience not present in the resume.
- Keep it to about 250-350 words.
- Sign off simply (e.g. "Sincerely,") without inventing contact details.
- Output only the letter text.
"""


def generate_cover_letter(resume_text, job_title, company_name, job_description, tone="formal"):
    """Call OpenAI and return the generated letter text.

    Raises CoverLetterError with a user-friendly message on failure.
    """
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise CoverLetterError(
            "The AI service is not configured yet. Add OPENAI_API_KEY to your .env file."
        )

    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover
        raise CoverLetterError("OpenAI library not installed.") from exc

    client = OpenAI(api_key=api_key)
    prompt = build_prompt(resume_text, job_title, company_name, job_description, tone)

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=700,
        )
    except Exception as exc:
        raise CoverLetterError(
            f"The AI service could not generate a letter right now: {exc}"
        ) from exc

    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise CoverLetterError("The AI returned an empty letter. Please try again.")
    return content
