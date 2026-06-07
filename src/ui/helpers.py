import re
import uuid
import wave
from pathlib import Path

import numpy as np


def clean_text_for_tts(answer: str, max_chars: int = 1500) -> str:
    if not answer:
        return ""

    # Ne pas lire les sources a voix haute
    text = re.split(r"\n\s*Sources\s*:", answer, maxsplit=1, flags=re.IGNORECASE)[0]

    # Ne pas lire les details techniques des erreurs
    text = re.split(
        r"\n\s*D.{0,2}tail technique\s*:",
        text,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    # Blocs de code et code inline
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)

    # Liens markdown : [texte](url) -> texte
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Gras / italique markdown
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)

    # Titres, citations, puces
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)

    # Espaces
    text = re.sub(r"\n{2,}", ". ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) > max_chars:
        shortened = text[:max_chars]
        if "." in shortened:
            shortened = shortened.rsplit(".", 1)[0] + "."
        text = shortened

    return text


def normalize_transcription(text: str) -> str:
    replacements = {
        "fishing": "phishing",
        "fiching": "phishing",
        "shing": "phishing",
        "vous fichiez": "le phishing",
        "ce que vous fichiez": "ce que le phishing",
        "phishingues": "phishing",
    }

    normalized = text

    for wrong, right in replacements.items():
        normalized = re.sub(
            rf"\b{re.escape(wrong)}\b",
            right,
            normalized,
            flags=re.IGNORECASE,
        )

    return normalized


def clean_source_name(source_name: str) -> str:
    return (
        source_name.strip()
        .strip("`")
        .strip("*")
        .strip("_")
        .strip()
    )


def save_pcm_to_wav(
    pcm_chunks: list[bytes],
    output_dir: Path,
    sample_rate: int = 24000,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{uuid.uuid4()}.wav"

    raw_audio = b"".join(pcm_chunks)
    audio_array = np.frombuffer(raw_audio, dtype=np.int16)

    with wave.open(str(file_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_array.tobytes())

    return file_path
