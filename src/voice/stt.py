from functools import lru_cache

from faster_whisper import WhisperModel


@lru_cache(maxsize=1)
def get_model() -> WhisperModel:
    return WhisperModel("small", device="cpu", compute_type="int8")


def transcribe(audio_path: str) -> str:
    segments, _ = get_model().transcribe(
        audio_path,
        language="fr",
        vad_filter=True,
    )

    return " ".join(segment.text for segment in segments).strip()