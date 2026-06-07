"""Standalone F.R.I.T.E.S web UI.

Run from the project root with:
    python -m uvicorn src.ui.web_app:app --reload --host 127.0.0.1 --port 8000

This replaces the Chainlit UI layer, but reuses the existing agent backend:
    src.agent.runner.ask_agent
"""

from __future__ import annotations

import re
import sys
import uuid
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.graph import llm  # noqa: E402
from src.agent.runner import ask_agent  # noqa: E402
from src.ui.helpers import normalize_transcription  # noqa: E402

STATIC_DIR = Path(__file__).resolve().parent / "web_static"
SOURCE_ROOTS = [
    PROJECT_ROOT / "data" / "knowledge" / "cybersec",
    PROJECT_ROOT / "data" / "knowledge" / "uphf",
]
SOURCE_LINE_PATTERN = re.compile(
    r"^\s*[-*•]?\s*(?P<source>[^,\n]+?)(?:\s*,\s*page\s*(?P<page>[^\n]+))?\s*$",
    re.MULTILINE | re.IGNORECASE,
)

app = FastAPI(title="F.R.I.T.E.S. UI", version="1.4.0")
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


class ChatRequest(BaseModel):
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str = Field(min_length=1, max_length=8000)


class SourceRef(BaseModel):
    name: str
    page: str | None = None
    url: str


class UiStep(BaseModel):
    title: str
    detail: str | None = None
    status: Literal["done", "warning", "error"] = "done"


class ChatResponse(BaseModel):
    conversation_id: str
    role: Literal["assistant"] = "assistant"
    content: str
    steps: list[UiStep] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)


class TitleRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class TitleResponse(BaseModel):
    title: str


class TranscriptionResponse(BaseModel):
    text: str


def _clean_title(raw_title: str, fallback_source: str) -> str:
    title = (raw_title or "").strip()
    title = title.splitlines()[0] if title else ""
    title = re.sub(r"^[\s\-–—•*\"'“”‘’]+", "", title)
    title = re.sub(r"[\s\-–—•*\"'“”‘’]+$", "", title)
    title = re.sub(r"\s+", " ", title)

    if not title or len(title) > 80:
        title = fallback_source.strip()

    words = re.findall(r"[\wÀ-ÖØ-öø-ÿ’'-]+", title, flags=re.UNICODE)[:9]
    title = " ".join(words).strip(" -–—")

    if not title:
        title = "Conversation cyber"

    return title[:64]


def _clean_source_name(source_name: str) -> str:
    return (
        (source_name or "")
        .strip()
        .strip("`")
        .strip("*")
        .strip("_")
        .strip()
        .removesuffix(".pdf")
        .strip()
    )


def _find_source_file(source_name: str) -> Path | None:
    cleaned = _clean_source_name(source_name)
    if not cleaned:
        return None

    for root in SOURCE_ROOTS:
        if not root.exists():
            continue
        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.stem == cleaned or file_path.name == cleaned:
                return file_path
    return None


def _extract_sources(answer: str) -> list[SourceRef]:
    if not answer or "source" not in answer.lower():
        return []

    parts = re.split(r"\n\s*Sources?\s*:\s*\n?", answer, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) < 2:
        return []

    sources_block = parts[1]
    results: list[SourceRef] = []
    seen: set[tuple[str, str | None]] = set()

    for line in sources_block.splitlines():
        line = line.strip()
        if not line:
            continue
        match = SOURCE_LINE_PATTERN.match(line)
        if not match:
            continue

        source_name = _clean_source_name(match.group("source"))
        page = (match.group("page") or "").strip() or None
        if not source_name:
            continue

        key = (source_name, page)
        if key in seen:
            continue
        seen.add(key)

        if _find_source_file(source_name):
            url = f"/api/source/{source_name}"
            if page:
                page_number = re.search(r"\d+", page)
                if page_number:
                    url += f"#page={page_number.group(0)}"
            results.append(SourceRef(name=source_name, page=page, url=url))

    return results


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "ui": "standalone", "agent": "src.agent.runner.ask_agent"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message vide.")

    conversation_id = request.conversation_id.strip() or str(uuid.uuid4())

    steps: list[UiStep] = [
        UiStep(title="Préparation de la requête", detail="Conversation récupérée et message préparé."),
        UiStep(title="Agent RAG / Ollama", detail="Recherche documentaire et génération de la réponse."),
    ]

    answer = await ask_agent(user_input=message, thread_id=conversation_id)
    sources = _extract_sources(answer)

    if sources:
        steps.append(
            UiStep(
                title="Sources affichables",
                detail=f"{len(sources)} source(s) PDF détectée(s) et reliée(s).",
            )
        )
    else:
        steps.append(
            UiStep(
                title="Sources affichables",
                detail="Aucune source PDF affichable détectée dans cette réponse.",
                status="warning",
            )
        )

    return ChatResponse(conversation_id=conversation_id, content=answer, steps=steps, sources=sources)


@app.post("/api/title", response_model=TitleResponse)
async def title(request: TitleRequest) -> TitleResponse:
    """Generate a short conversation title using the configured Ollama model."""
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message vide.")

    fallback = _clean_title(message, "Conversation cyber")
    prompt = (
        "Tu génères uniquement un titre court de conversation en français. "
        "Maximum 9 mots. Pas de guillemets. Pas de ponctuation finale. "
        "Ne réponds qu'avec le titre.\n\n"
        f"Message utilisateur : {message}"
    )

    try:
        result = await llm.ainvoke(prompt)
        raw_title = getattr(result, "content", str(result))
        generated = _clean_title(raw_title, fallback)
    except Exception:
        generated = fallback

    return TitleResponse(title=generated)


@app.post("/api/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...)) -> TranscriptionResponse:
    """Transcribe browser-recorded audio with the existing local STT module."""
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Le fichier envoyé n'est pas un audio.")

    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    audio_dir = PROJECT_ROOT / "tmp" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = audio_dir / f"{uuid.uuid4()}{suffix}"

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Audio vide.")
    audio_path.write_bytes(data)

    try:
        from src.voice.stt import transcribe  # noqa: WPS433

        text = await run_in_threadpool(transcribe, str(audio_path))
        text = normalize_transcription(text)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "La transcription vocale locale a échoué. Vérifie faster-whisper, ffmpeg/PyAV "
                f"et le micro. Détail : {exc}"
            ),
        ) from exc

    if not text:
        raise HTTPException(status_code=422, detail="Aucune parole exploitable détectée.")

    return TranscriptionResponse(text=text)


@app.get("/api/source/{source_name:path}")
async def source_file(source_name: str) -> FileResponse:
    source_name = _clean_source_name(source_name)
    file_path = _find_source_file(source_name)
    if not file_path:
        raise HTTPException(status_code=404, detail=f"Source introuvable : {source_name}")

    media_type = "application/pdf" if file_path.suffix.lower() == ".pdf" else "application/octet-stream"
    return FileResponse(path=file_path, media_type=media_type, filename=file_path.name)


@app.get("/{full_path:path}")
async def spa_fallback(full_path: str) -> FileResponse:
    # Permet le rafraîchissement de l'app côté navigateur sans casser la SPA.
    candidate = STATIC_DIR / full_path
    if candidate.exists() and candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(STATIC_DIR / "index.html")
