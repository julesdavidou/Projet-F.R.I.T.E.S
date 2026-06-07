from faster_whisper import WhisperModel

# modèle chargé une seule fois (important)
model = WhisperModel("small", device="cpu", compute_type="int8")

def transcribe(audio_path: str) -> str:
    segments, info = model.transcribe(
        audio_path,
        language="fr",
        vad_filter=True
    )

    text = " ".join(segment.text for segment in segments).strip()

    return text