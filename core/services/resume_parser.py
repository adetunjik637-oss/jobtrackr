"""Extract plain text from an uploaded resume (PDF or DOCX)."""
import os


class ResumeParseError(Exception):
    pass


def extract_text(django_file):
    """Return plain text from a Django UploadedFile or FieldFile.

    Supports .pdf and .docx. Raises ResumeParseError on unsupported types
    or extraction failure.
    """
    name = (getattr(django_file, "name", "") or "").lower()
    ext = os.path.splitext(name)[1]

    if ext == ".pdf":
        return _extract_pdf(django_file)
    if ext in (".docx",):
        return _extract_docx(django_file)
    if ext in (".txt",):
        return _read_text(django_file)
    raise ResumeParseError(
        "Unsupported file type. Please upload a PDF, DOCX, or TXT file."
    )


def _read_text(django_file):
    django_file.seek(0)
    raw = django_file.read()
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="ignore").strip()
    return str(raw).strip()


def _extract_pdf(django_file):
    try:
        import pdfplumber
    except ImportError as exc:  # pragma: no cover
        raise ResumeParseError("PDF support not installed.") from exc

    django_file.seek(0)
    text_parts = []
    try:
        with pdfplumber.open(django_file) as pdf:
            for page in pdf.pages:
                text_parts.append(page.extract_text() or "")
    except Exception as exc:
        raise ResumeParseError(f"Could not read the PDF: {exc}") from exc
    text = "\n".join(text_parts).strip()
    if not text:
        raise ResumeParseError(
            "No text found in the PDF. If it is a scanned image, "
            "please upload a text-based PDF or DOCX."
        )
    return text


def _extract_docx(django_file):
    try:
        import docx
    except ImportError as exc:  # pragma: no cover
        raise ResumeParseError("DOCX support not installed.") from exc

    django_file.seek(0)
    try:
        document = docx.Document(django_file)
    except Exception as exc:
        raise ResumeParseError(f"Could not read the DOCX: {exc}") from exc
    text = "\n".join(p.text for p in document.paragraphs).strip()
    if not text:
        raise ResumeParseError("The DOCX appears to be empty.")
    return text
