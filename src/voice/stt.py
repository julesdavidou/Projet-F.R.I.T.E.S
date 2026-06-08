from faster_whisper import WhisperModel

# On déclare la variable globale, mais on ne charge rien au démarrage car sinon ça fait charger le modèle à la CI (et ça prend du temps)
_model = None

def get_model():
    """Charge le modèle Whisper uniquement si ce n'est pas déjà fait (Lazy Loading)."""
    global _model
    if _model is None:
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    return _model

def transcribe(audio_path: str) -> str:
    # On récupère le modèle au moment où on en a besoin
    model = get_model()
    
    segments, info = model.transcribe(
        audio_path,
        language="fr",
        vad_filter=True
    )

    text = " ".join(segment.text for segment in segments).strip()

    return text