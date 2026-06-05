import subprocess
import uuid
from pathlib import Path

model_path = Path("models/piper/fr_FR-upmc-medium.onnx")
config_path = Path("models/piper/fr_FR-upmc-medium.onnx.json")

sortie_DIR = Path("tmp/audio")


# --------------------
# VALIDATIONS
# --------------------
def verif_text(text: str) -> str:
    text = text.strip()
    if not text:
        raise ValueError("Le texte est vide")
    return text


def verif_model():
    if not model_path.exists():
        raise FileNotFoundError(model_path)
    if not config_path.exists():
        raise FileNotFoundError(config_path)


def verif_sortie_directory():
    sortie_DIR.mkdir(parents=True, exist_ok=True)


# --------------------
# OUTPUT PATH
# --------------------
def gen_sortie_path() -> Path:
    return sortie_DIR / f"{uuid.uuid4()}.wav"


# --------------------
# PIPER EXECUTION
# --------------------
def generation_audio(text: str, sortie_path: Path):
    subprocess.run(
        [
            "piper",
            "--model", str(model_path),
            "--output_file", str(sortie_path),
        ],
        input=text,
        text=True,
        check=True
    )


def verif_fichier_audio(path: Path):
    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError("Le fichier audio n'a pas été généré correctement")


# --------------------
# MAIN
# --------------------
def synthesize(reponse_text: str) -> Path:
    reponse_text = verif_text(reponse_text)

    verif_model()
    verif_sortie_directory()

    sortie_path = gen_sortie_path()

    generation_audio(reponse_text, sortie_path)

    verif_fichier_audio(sortie_path)

    return sortie_path