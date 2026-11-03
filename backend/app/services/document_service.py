"""Document parsing, text extraction, cleaning, and chunking service."""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple
from fastapi import HTTPException, UploadFile, status
import fitz  # PyMuPDF
import docx

from app.core.config import settings


class DocumentService:
    """Handles file validation, text extraction, cleaning, and chunking."""

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        self.allowed_extensions = set(settings.ALLOWED_DOCUMENT_EXTENSIONS)

    def validate_file(self, file: UploadFile) -> Tuple[str, str]:
        """Validate filename, extension, and return safe sanitized filename and extension."""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file has no filename.",
            )

        # Prevent path traversal
        clean_filename = Path(file.filename).name
        ext = Path(clean_filename).suffix.lower()

        if ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{ext}' is unsupported. Allowed formats: {', '.join(sorted(self.allowed_extensions))}",
            )

        return clean_filename, ext

    def clean_text(self, text: str) -> str:
        """Normalizes whitespace and removes unprintable control characters."""
        if not text:
            return ""
        # Remove null bytes and non-printable control characters except standard whitespace
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", " ", text)
        # Collapse multiple spaces and excessive blank lines
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def extract_text(self, file_path: str, file_ext: str) -> List[Dict[str, Any]]:
        """Extract text page by page (or section by section) from PDF, DOCX, or TXT."""
        pages_content: List[Dict[str, Any]] = []

        if file_ext == ".pdf":
            try:
                doc = fitz.open(file_path)
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    page_text = self.clean_text(page.get_text())
                    if page_text:
                        pages_content.append({"page": page_num + 1, "text": page_text})
                doc.close()
            except Exception as e:
                raise RuntimeError(f"Failed to extract text from PDF: {str(e)}")

        elif file_ext == ".docx":
            try:
                doc = docx.Document(file_path)
                full_paragraphs = []
                for p in doc.paragraphs:
                    cleaned = self.clean_text(p.text)
                    if cleaned:
                        full_paragraphs.append(cleaned)

                # Also extract table text if present
                for table in doc.tables:
                    for row in table.rows:
                        row_text = " | ".join(
                            self.clean_text(cell.text)
                            for cell in row.cells
                            if self.clean_text(cell.text)
                        )
                        if row_text:
                            full_paragraphs.append(row_text)

                combined_text = "\n\n".join(full_paragraphs)
                if combined_text:
                    pages_content.append({"page": 1, "text": combined_text})
            except Exception as e:
                raise RuntimeError(f"Failed to extract text from DOCX: {str(e)}")

        elif file_ext == ".txt":
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = self.clean_text(f.read())
                    if content:
                        pages_content.append({"page": 1, "text": content})
            except Exception as e:
                raise RuntimeError(f"Failed to read TXT file: {str(e)}")

        return pages_content

    def chunk_document(
        self,
        pages_content: List[Dict[str, Any]],
        chunk_size: int = 900,
        chunk_overlap: int = 150,
    ) -> List[Dict[str, Any]]:
        """Splits document content into overlapping chunks preserving page metadata."""
        chunks: List[Dict[str, Any]] = []
        chunk_index = 0

        for item in pages_content:
            page_num = item["page"]
            text = item["text"]
            if not text:
                continue

            # If text is smaller than chunk size, treat whole page as one chunk
            if len(text) <= chunk_size:
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "page": page_num,
                        "text": text,
                    }
                )
                chunk_index += 1
                continue

            start = 0
            while start < len(text):
                end = start + chunk_size
                chunk_text = text[start:end]

                # Try to break at sentence or paragraph boundary if possible
                if end < len(text):
                    last_period = max(
                        chunk_text.rfind(". "),
                        chunk_text.rfind(".\n"),
                        chunk_text.rfind("\n\n"),
                    )
                    if last_period != -1 and last_period > chunk_size // 2:
                        chunk_text = chunk_text[: last_period + 1]
                        end = start + last_period + 1

                cleaned_chunk = chunk_text.strip()
                if cleaned_chunk:
                    chunks.append(
                        {
                            "chunk_index": chunk_index,
                            "page": page_num,
                            "text": cleaned_chunk,
                        }
                    )
                    chunk_index += 1

                start += max(len(chunk_text) - chunk_overlap, chunk_overlap)

        return chunks


document_service = DocumentService()
