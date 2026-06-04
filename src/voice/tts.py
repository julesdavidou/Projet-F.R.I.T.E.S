import subprocess
import uuid
from pathlib import Path
from piper.voice import PiperVoice

model_path = Path("models/piper/fr_FR-upmc-medium.onnx")
config_path = Path("models/piper/fr_FR-upmc-medium.onnx.json")

sortie_DIR = Path("tmp/audio")



def verif_text(text): #verifie que le text est non vide
    text = text.strip()

    if not text:
        raise ValueError("le text est vide")
    
    return text

def verif_model(): #vérifie que le modele est disponible
    if not model_path.exists():
        raise FileNotFoundError(model_path)

    if not config_path.exists():
        raise FileNotFoundError(config_path)

def verif_sortie_directory():
    sortie_DIR.mkdir(
        parents = True,
        exist_ok = True
    )

def gen_sortie_path(): #chemin de sortie
    nom_fichier = f"{uuid.uuid4()}.wav"

    return sortie_DIR/nom_fichier

def charge_voix():
    return PiperVoice.load(
        str(model_path)
    )

def generation_audio(text: str,sortie_path,model_path):
     subprocess.run(
        [
            "piper",
            "--model", model_path,
            "--output_file", str(sortie_path),
        ],
        input=text,
        text=True,
        check=True
    )

def verif_fichier_audio(sortie_path):
    if not sortie_path.exists():
        raise RuntimeError("le fichier audio n'a pas été enregistrer")

def synthesize(reponse_text):
    reponse_text = verif_text(reponse_text)

    verif_model()
    verif_sortie_directory()

    sortie_path = gen_sortie_path()

    charge_voix()

    audio = generation_audio(reponse_text,sortie_path,model_path)

    verif_fichier_audio(sortie_path)

    return sortie_path

#audio_path = synthesize(reponse_text)