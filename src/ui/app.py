import sys
import uuid
import wave
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import chainlit as cl
import numpy as np

from src.agent.runner import ask_agent

SOURCE_ROOTS = [
    Path("data/knowledge/cybersec"),
    Path("data/knowledge/uphf"),
]

SOURCE_LINE_PATTERN = re.compile(
    r"^\s*[-•]\s*(?P<source>[^,\n]+)(?:,\s*page\s*(?P<page>[^\n]+))?",
    re.MULTILINE,
)



def save_pcm_to_wav(pcm_chunks: list[bytes], sample_rate: int = 24000) -> Path:
    audio_dir = Path("tmp/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)

    file_path = audio_dir / f"{uuid.uuid4()}.wav"

    raw_audio = b"".join(pcm_chunks)
    audio_array = np.frombuffer(raw_audio, dtype=np.int16)

    with wave.open(str(file_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_array.tobytes())

    return file_path


async def handle_user_text(user_input: str) -> str:
    thread_id = cl.user_session.get("thread_id")

    response = await ask_agent(
        user_input=user_input,
        thread_id=thread_id,
    )

    elements = build_source_elements(response)

    await cl.Message(
        content=response,
        elements=elements,
    ).send()

    return response


@cl.on_chat_start
async def on_chat_start():
    thread_id = str(uuid.uuid4())

    cl.user_session.set("thread_id", thread_id)
    cl.user_session.set("audio_buffer", [])

    await cl.Message(
        content=(
            "Bienvenue sur F.R.I.T.E.S. — Agent de sécurité numérique UPHF.\n\n"
            "Pose-moi une question sur la cybersécurité, le phishing, les mots de passe, "
            "la MFA, eduVPN ou les bonnes pratiques numériques."
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    await handle_user_text(message.content)


@cl.on_audio_chunk
async def on_audio_chunk(chunk):
    buffer = cl.user_session.get("audio_buffer") or []
    buffer.append(chunk.data)
    cl.user_session.set("audio_buffer", buffer)


@cl.on_audio_end
async def on_audio_end():
    buffer = cl.user_session.get("audio_buffer") or []

    if not buffer:
        await cl.Message(content="Je n'ai pas reçu d'audio exploitable.").send()
        return

    cl.user_session.set("audio_buffer", [])

    wav_path = save_pcm_to_wav(buffer)

    try:
        from src.voice.stt import transcribe
    except ImportError as exc:
        await cl.Message(
            content=f"Le module de transcription vocale n'est pas disponible : {exc}"
        ).send()
        return

    text = transcribe(str(wav_path))

    if not text:
        await cl.Message(content="Je n'ai pas réussi à transcrire l'audio.").send()
        return

    await cl.Message(content=f"Transcription : {text}").send()

    await handle_user_text(text)


def find_source_file(source_name: str) -> Path | None:
    source_name = source_name.strip()

    for root in SOURCE_ROOTS:
        if not root.exists():
            continue

        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue

            if file_path.stem == source_name:
                return file_path

    return None


def build_source_elements(answer: str) -> list:
    if "Sources" not in answer:
        return []

    sources_block = answer.split("Sources", 1)[1]
    elements = []
    seen = set()

    for match in SOURCE_LINE_PATTERN.finditer(sources_block):
        source_name = match.group("source").strip()

        if source_name in seen:
            continue

        seen.add(source_name)

        file_path = find_source_file(source_name)

        if not file_path:
            continue

        if file_path.suffix.lower() == ".pdf":
            elements.append(
                cl.Pdf(
                    name=source_name,
                    path=str(file_path),
                    display="side",
                )
            )
        else:
            elements.append(
                cl.File(
                    name=file_path.name,
                    path=str(file_path),
                    display="inline",
                )
            )

    return elements