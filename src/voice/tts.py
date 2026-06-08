import shutil
import subprocess
import uuid
from pathlib import Path


MODEL_PATH = Path("models/piper/fr_FR-upmc-medium.onnx")
CONFIG_PATH = Path("models/piper/fr_FR-upmc-medium.onnx.json")
OUTPUT_DIR = Path("tmp/audio")


def is_tts_available() -> bool:
    return (
        shutil.which("piper") is not None
        and MODEL_PATH.exists()
        and CONFIG_PATH.exists()
    )


def synthesize(text: str) -> Path:
    text = text.strip()

    if not text:
        raise ValueError("Le texte à vocaliser est vide.")

    if shutil.which("piper") is None:
        raise FileNotFoundError("La commande 'piper' est introuvable.")

    if not MODEL_PATH.exists():
        raise FileNotFoundError(MODEL_PATH)

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(CONFIG_PATH)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIR / f"{uuid.uuid4()}.wav"

    subprocess.run(
        [
            "piper",
            "--model",
            str(MODEL_PATH),
            "--output_file",
            str(output_path),
        ],
        input=text,
        text=True,
        check=True,
    )

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("Le fichier audio Piper n'a pas été généré correctement.")

    return output_path