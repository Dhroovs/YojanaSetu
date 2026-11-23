import hashlib
import ipaddress
import logging
import re
import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
import pymupdf
import truststore
from bs4 import BeautifulSoup

from app.ai.models import Chunk, SourceManifest, SourceRecord
from app.ai.vectors import VectorIndex, index_version
from app.config import Settings

logger = logging.getLogger(__name__)


def official_url(url: str, resolve=False):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if (
        parsed.scheme != "https"
        or parsed.port not in {None, 443}
        or parsed.username
        or parsed.password
        or not host.endswith((".gov.in", ".nic.in"))
    ):
        raise ValueError("Only HTTPS .gov.in/.nic.in official sources are allowed")
    if resolve:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
            raise ValueError("Source resolves to a non-public address")


def download(url: str, max_bytes: int) -> tuple[bytes, str]:
    # CLI-only fetching: never fetch a URL supplied by an ordinary AI request.
    with httpx.Client(
        timeout=30,
        follow_redirects=False,
        trust_env=False,
        verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
    ) as client:
        for _ in range(4):
            official_url(url, resolve=True)
            with client.stream(
                "GET", url, headers={"User-Agent": "YojanaSetuSourceReview/0.2"}
            ) as r:
                if r.is_redirect:
                    from urllib.parse import urljoin

                    url = urljoin(url, r.headers["location"])
                    continue
                r.raise_for_status()
                mime = r.headers.get("content-type", "").split(";")[0].lower()
                if mime not in {"application/pdf", "text/html", "application/xhtml+xml"}:
                    raise ValueError("Source must be a PDF or HTML document")
                data = bytearray()
                for part in r.iter_bytes():
                    data.extend(part)
                    if len(data) > max_bytes:
                        raise ValueError("Source exceeds ingestion size limit")
                return bytes(data), "pdf" if mime == "application/pdf" else "html"
    raise ValueError("Too many redirects; review the final official source URL")


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\x00", " ")).strip()


def extract(data: bytes, kind: str, max_bytes: int, max_pages: int) -> list[tuple[int | None, str]]:
    if not data or len(data) > max_bytes:
        raise ValueError("Empty document or ingestion size limit exceeded")
    if kind == "pdf":
        if not data.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF signature")
        try:
            with pymupdf.open(stream=data, filetype="pdf") as document:
                if document.needs_pass or document.page_count > max_pages:
                    raise ValueError("Encrypted PDF or page limit exceeded")
                pages = [(i + 1, clean_text(page.get_text())) for i, page in enumerate(document)]
        except (pymupdf.FileDataError, RuntimeError) as exc:
            raise ValueError("Unable to extract PDF text") from exc
    elif kind == "html":
        soup = BeautifulSoup(data, "html.parser")
        for tag in soup(
            ["script", "style", "nav", "footer", "input", "select", "button", "noscript"]
        ):
            tag.decompose()
        body = soup.find("main") or soup.find("body") or soup
        pages = [(None, clean_text(body.get_text(" ")))]
    else:
        raise ValueError("Only PDF and HTML documents are supported")
    pages = [(page, text) for page, text in pages if text]
    if not pages:
        raise ValueError("No extractable text. Scanned PDFs need reviewed OCR before ingestion.")
    if sum(len(text) for _, text in pages) > 2_000_000:
        raise ValueError("Extracted text exceeds safety limit")
    return pages


def chunk_document(
    pages, manifest: SourceManifest, content_hash: str, version: str, size=1100, overlap=200
) -> list[Chunk]:
    if size <= overlap or overlap < 0:
        raise ValueError("Chunk size must exceed nonnegative overlap")
    chunks = []
    for page, text in pages:
        for offset in range(0, len(text), size - overlap):
            part = text[offset : offset + size]
            if not part:
                continue
            chunk_id = hashlib.sha256(
                f"{manifest.source_id}:{version}:{page}:{offset}".encode()
            ).hexdigest()
            chunks.append(
                Chunk(
                    id=chunk_id,
                    text=part,
                    source_id=manifest.source_id,
                    scheme_id=manifest.scheme_id,
                    document_title=manifest.document_title,
                    official_url=str(manifest.official_url),
                    page=page,
                    content_hash=content_hash,
                    index_version=version,
                    verification_status=manifest.verification_status,
                    scope=manifest.scope,
                )
            )
    return chunks


async def ingest(
    manifest: SourceManifest,
    data: bytes,
    kind: str,
    store,
    index: VectorIndex,
    settings: Settings,
    *,
    allow_synthetic=False,
):
    if manifest.verification_status == "synthetic":
        if not allow_synthetic or not index.collection.name.startswith("synthetic_"):
            raise ValueError("Synthetic sources require an isolated synthetic_ test collection")
    else:
        official_url(str(manifest.official_url))
        if manifest.scheme_id.startswith("demo-"):
            raise ValueError("Verified sources cannot replace demo schemes")
        if manifest.application_url:
            official_url(str(manifest.application_url))
    pages = extract(data, kind, settings.ingestion_max_bytes, settings.ingestion_max_pages)
    if manifest.verification_status == "verified" and any(
        "synthetic test document" in text.casefold() for _, text in pages
    ):
        raise ValueError("Synthetic test documents cannot be ingested as verified sources")
    content_hash = hashlib.sha256(data).hexdigest()
    version = index_version(content_hash, manifest.model_dump_json(), index.embeddings.identity)
    chunks = chunk_document(pages, manifest, content_hash, version)
    for quote in [r.quote for r in manifest.rules] + list(manifest.field_evidence.values()):
        if not any(clean_text(quote) in c.text for c in chunks):
            raise ValueError("Curated rule/field quotation is absent from a source chunk")
    for rule in manifest.rules:
        if type(rule.value) is int:
            numbers = re.findall(r"\d+", rule.quote.replace(",", ""))
            if str(rule.value) not in numbers:
                raise ValueError("Numeric rule threshold is not present in its supporting quote")
    for field in (
        "beneficiary_categories",
        "age_restrictions",
        "income_restrictions",
        "occupation_requirements",
        "gender_requirements",
        "disability_conditions",
        "required_documents",
        "benefits",
        "application_process",
        "application_url",
    ):
        if getattr(manifest, field) is not None and field not in manifest.field_evidence:
            raise ValueError(f"Curated {field} requires a supporting field_evidence quote")
    previous = await store.source(manifest.source_id)
    unchanged = bool(
        previous
        and previous.index_version == version
        and len(index.source_chunks(manifest.source_id, version)) == len(chunks)
    )
    record = SourceRecord(
        **manifest.model_dump(),
        retrieved_at=datetime.now(timezone.utc),
        content_hash=content_hash,
        index_version=version,
        chunk_count=len(chunks),
    )
    # Embed/write first; if activation fails these chunks are invisible to the matcher.
    if not unchanged:
        index.upsert(chunks)
    scheme = {
        "id": manifest.scheme_id,
        "title": manifest.scheme_name,
        "category": manifest.category,
        "summary": "Official source indexed. Read cited evidence; this is preliminary guidance.",
        "eligibility": [r.quote for r in manifest.rules],
        "documents": manifest.required_documents or [],
        "guidance": manifest.application_process or [],
        "is_demo": False,
        "source_url": str(manifest.official_url),
        "department": manifest.department,
        "geographic_coverage": manifest.geographic_coverage,
        "beneficiary_categories": manifest.beneficiary_categories,
        "age_restrictions": manifest.age_restrictions,
        "income_restrictions": manifest.income_restrictions,
        "occupation_requirements": manifest.occupation_requirements,
        "gender_requirements": manifest.gender_requirements,
        "disability_conditions": manifest.disability_conditions,
        "benefits": manifest.benefits,
        "application_url": str(manifest.application_url) if manifest.application_url else None,
        "source_references": [manifest.source_id],
        "last_verified_at": str(manifest.reviewed_at),
        "information_completeness": manifest.completeness,
        "scope": manifest.scope,
    }
    await store.activate(record, scheme)
    index.remove_old(manifest.source_id, version)
    logger.info("Source %s: %s chunks, unchanged=%s", manifest.source_id, len(chunks), unchanged)
    return {
        "status": "unchanged" if unchanged else "indexed",
        "source_id": manifest.source_id,
        "chunks": len(chunks),
        "content_hash": content_hash,
    }
