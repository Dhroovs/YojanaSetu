import hashlib
import io
import os
import re
import warnings
from pathlib import Path
from typing import Protocol
from uuid import uuid4

import pymupdf
from fastapi import HTTPException
from PIL import Image, ImageStat, UnidentifiedImageError


class FileStorage(Protocol):
    def put(self, data: bytes, extension: str) -> str: ...
    def path(self, key: str) -> Path: ...
    def delete(self, key: str): ...


class LocalPrivateStorage:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        project = Path(__file__).resolve().parents[3]
        if self.directory.is_relative_to(project / "frontend") or self.directory.is_relative_to(
            project / ".git"
        ):
            raise ValueError(
                "Private documents must not be stored in the frontend or Git metadata directory"
            )
        self.directory.mkdir(parents=True, exist_ok=True)

    def path(self, key):
        if not re.fullmatch(r"[a-f0-9]{32}\.(pdf|png|jpg)", key):
            raise ValueError("Invalid private storage key")
        path = self.directory / key
        if path.is_symlink() or path.resolve().parent != self.directory:
            raise ValueError("Invalid private storage path")
        return path

    def put(self, data, extension):
        key = f"{uuid4().hex}.{extension}"
        fd = os.open(self.path(key), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        return key

    def delete(self, key):
        self.path(key).unlink(missing_ok=True)


def inspect_document(data: bytes, media_type: str, settings):
    if not data or len(data) > settings.document_max_bytes:
        raise HTTPException(413, "Empty file or document size limit exceeded.")
    content_hash = hashlib.sha256(data).hexdigest()
    if media_type == "application/pdf":
        if not data.startswith(b"%PDF-"):
            raise HTTPException(422, "File contents do not match PDF format.")
        try:
            with pymupdf.open(stream=data, filetype="pdf") as pdf:
                if pdf.needs_pass or not 1 <= pdf.page_count <= 50:
                    raise HTTPException(422, "PDF must be unencrypted and contain 1–50 pages.")
                if pdf.embfile_count():
                    raise HTTPException(422, "PDF attachments are not accepted.")
                for xref in range(1, pdf.xref_length()):
                    action = pdf.xref_get_key(xref, "S")[1]
                    if action in {"/JavaScript", "/Launch"}:
                        raise HTTPException(422, "PDF executable actions are not accepted.")
                # Never execute, store or send extracted text to a model.
                readable = any(bool(page.get_text().strip()) for page in pdf)
                notes = [
                    "PDF text is extractable."
                    if readable
                    else "No extractable text; a scanned PDF needs human review."
                ]
                if settings.enable_document_ocr and not readable:
                    try:
                        # Optional system Tesseract. Only a readability boolean leaves this call.
                        readable = bool(pdf[0].get_textpage_ocr().extractText().strip())
                        notes.append(
                            "Optional OCR readability check completed; no OCR text retained."
                        )
                    except Exception:
                        notes.append("OCR unavailable; human review is required.")
        except (pymupdf.FileDataError, RuntimeError, ValueError) as exc:
            raise HTTPException(422, "PDF cannot be safely read. Try another file.") from exc
        return (
            data,
            "pdf",
            content_hash,
            "technically_readable" if readable else "needs_human_review",
            notes,
        )
    if media_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(415, "Only PDF, JPEG and PNG are allowed.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data), formats=["PNG", "JPEG"]) as image:
                expected = "JPEG" if media_type == "image/jpeg" else "PNG"
                if image.format != expected or getattr(image, "n_frames", 1) != 1:
                    raise ValueError("Mismatched or animated image")
                width, height = image.size
                if width * height > 20_000_000:
                    raise ValueError("Image pixel limit exceeded")
                image.verify()
            with Image.open(io.BytesIO(data), formats=["PNG", "JPEG"]) as image:
                image = image.convert("RGB")
                sample = image.copy()
                sample.thumbnail((400, 400))
                contrast = ImageStat.Stat(sample.convert("L")).stddev[0]
                uncertain = min(width, height) < 400 or contrast < 8
                buffer = io.BytesIO()
                image.save(buffer, format=expected, exif=b"")
                clean = buffer.getvalue()
                if len(clean) > settings.document_max_bytes:
                    raise ValueError("Normalized image exceeds size limit")
        notes = [f"Decoded {width} × {height} image; metadata removed."]
        if uncertain:
            notes.append(
                "Low resolution or low contrast; retry with a clearer image or request review."
            )
        return (
            clean,
            "jpg" if expected == "JPEG" else "png",
            content_hash,
            ("needs_human_review" if uncertain else "technically_readable"),
            notes,
        )
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise HTTPException(
            422, "Image is invalid, too large or cannot be safely decoded."
        ) from exc
