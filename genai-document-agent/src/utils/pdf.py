"""
utils/pdf.py — PDF reading and writing helpers.
"""

from __future__ import annotations

import os
import tempfile
import textwrap

from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from .text import clean_markdown


def extract_pdf_text(uploaded_file) -> str:
    """Extract plain text from an uploaded PDF file object.

    Returns an empty string and raises no exceptions on failure —
    callers should check for an empty return value.
    """
    try:
        reader = PdfReader(uploaded_file)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text.strip()
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Could not read PDF: {exc}") from exc


def generate_pdf_from_text(text: str, filename: str = "output.pdf") -> str:
    """Render *text* into a PDF saved in the system temp directory.

    Returns the absolute path of the written file.
    """
    output_path = os.path.join(tempfile.gettempdir(), filename)
    c = canvas.Canvas(output_path, pagesize=letter)
    y_position = 750

    for line in clean_markdown(text).split("\n"):
        wrapped_lines = textwrap.wrap(line, width=90) or [""]
        for segment in wrapped_lines:
            if y_position < 50:
                c.showPage()
                y_position = 750
            c.drawString(50, y_position, segment)
            y_position -= 15

    c.save()
    return output_path
