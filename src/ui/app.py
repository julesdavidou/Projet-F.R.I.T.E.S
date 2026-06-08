import asyncio
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
from src.ui.helpers import clean_text_for_tts, normalize_transcription, clean_source_name

SOURCE_ROOTS = [
    Path("data/knowledge/cybersec"),
    Path("data/knowledge/uphf"),
]

SOURCE_LINE_PATTERN = re.compile(
    r"^\s*[-*•]\s*(?P<source>[^,\n]+?)(?:\s*,\s*page\s*(?P<page>[^\n]+))?\s*$",
    re.MULTILINE | re.IGNORECASE,
)

def clean_source_name(source_name: str) -> str:
    return (
        source_name.strip()
        .strip("`")
        .strip("*")
        .strip("_")
        .strip()
    )

def new_generation_id() -> str:
    generation_id = str(uuid.uuid4())
    cl.user_session.set("generation_id", generation_id)
    cl.user_session.set("stop_requested", False)
    return generation_id


def is_generation_active(generation_id: str) -> bool:
    return (
        cl.user_session.get("generation_id") == generation_id
        and not cl.user_session.get("stop_requested")
    )


@cl.on_stop
async def on_stop():
    cl.user_session.set("stop_requested", True)
    cl.user_session.set("generation_id", str(uuid.uuid4()))

    task = cl.user_session.get("current_generation_task")

    if task and not task.done():
        task.cancel()
        print("[STOP] Tâche de génération annulée.", flush=True)
    else:
        print("[STOP] Aucune tâche active à annuler.", flush=True)


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
    generation_id = new_generation_id()
    thread_id = cl.user_session.get("thread_id")

    async with cl.Step(name="Préparation de la requête", type="run") as step:
        step.input = user_input
        step.output = "Session récupérée, mémoire conversationnelle prête."

    task = asyncio.create_task(
        ask_agent(
            user_input=user_input,
            thread_id=thread_id,
        )
    )
    cl.user_session.set("current_generation_task", task)

    try:
        async with cl.Step(name="Agent LangGraph", type="llm") as step:
            step.input = user_input
            response = await task
            step.output = "Réponse générée par l’agent."

    except asyncio.CancelledError:
        cl.user_session.set("stop_requested", True)
        print("[STOP] Génération annulée avant réponse.", flush=True)
        return ""

    except Exception as exc:
        print(f"[AGENT] Erreur pendant la génération : {exc}", flush=True)
        return (
            "Une erreur est survenue pendant la génération de la réponse. "
            "Vérifie qu’Ollama est lancé et que le modèle configuré est disponible."
        )

    finally:
        if cl.user_session.get("current_generation_task") is task:
            cl.user_session.set("current_generation_task", None)

    if not is_generation_active(generation_id):
        print("[STOP] Réponse ignorée car la génération a été stoppée.", flush=True)
        return ""

    async with cl.Step(name="Recherche des sources affichables", type="tool") as step:
        elements = build_source_elements(response)

        if elements:
            source_names = [element.name for element in elements]

            step.output = (
                    f"{len(elements)} fichier(s) source affichable(s) trouvé(s) :\n"
                    + "\n".join(f"- {name}" for name in source_names)
            )

            # Important : attache les PDF au step aussi
            step.elements = elements

            # Optionnel : ouvre directement le panneau latéral avec les sources
            await cl.ElementSidebar.set_elements(elements)
            await cl.ElementSidebar.set_title("Sources RAG")
        else:
            step.output = "Aucun fichier source affichable trouvé."

    tts_text = clean_text_for_tts(response)

    if response.startswith("Je n'arrive pas à interroger correctement le modèle local Ollama"):
        tts_text = ""

    if tts_text and is_generation_active(generation_id):
        try:
            from src.voice.tts import is_tts_available, synthesize

            async with cl.Step(name="Synthèse vocale", type="tool") as step:
                if is_tts_available():
                    audio_path = synthesize(tts_text)
                    elements.append(
                        cl.Audio(
                            name="Réponse vocale",
                            path=str(audio_path),
                            display="inline",
                        )
                    )
                    step.output = f"Audio généré : {audio_path}"
                else:
                    step.output = "Synthèse vocale indisponible : Piper ou modèle vocal absent."

        except Exception as exc:
            print(f"[TTS] Synthèse vocale ignorée : {exc}", flush=True)

    if not is_generation_active(generation_id):
        print("[STOP] Message final ignoré car la génération a été stoppée.", flush=True)
        return ""

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

    # Pas de message de bienvenue ici :
    # l'écran d'accueil F.R.I.T.E.S. est rendu par public/frite-shell.js.


@cl.on_message
async def on_message(message: cl.Message):
    await handle_user_text(message.content)

@cl.on_audio_start
async def on_audio_start():
    cl.user_session.set("audio_buffer", [])
    return True

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
    text = normalize_transcription(text)

    if not text:
        await cl.Message(content="Je n'ai pas réussi à transcrire l'audio.").send()
        return

    async with cl.Step(name="Transcription vocale", type="tool") as step:
        step.output = text

    await handle_user_text(text)


def find_source_file(source_name: str) -> Path | None:
    source_name = clean_source_name(source_name)

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
        print("[SOURCES] Aucun bloc Sources trouvé.", flush=True)
        return []

    sources_block = answer.split("Sources", 1)[1]
    elements = []
    seen = set()

    for match in SOURCE_LINE_PATTERN.finditer(sources_block):
        source_name = clean_source_name(match.group("source"))
        print(f"[SOURCES] Source détectée : {source_name}", flush=True)

        if source_name in seen:
            continue

        seen.add(source_name)

        file_path = find_source_file(source_name)

        if not file_path:
            print(f"[SOURCES] Fichier introuvable pour : {source_name}", flush=True)
            continue

        print(f"[SOURCES] Fichier trouvé : {file_path}", flush=True)

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

def clean_text_for_tts(answer: str, max_chars: int = 2500) -> str:
    """Nettoie la réponse Markdown pour la synthèse vocale.

    - enlève le bloc Sources
    - enlève les astérisques Markdown
    - enlève les liens Markdown
    - limite la longueur pour éviter une synthèse trop longue
    """

    if not answer:
        return ""

    # Ne pas lire les sources à voix haute
    text = re.split(r"\n\s*Sources\s*:", answer, maxsplit=1, flags=re.IGNORECASE)[0]

    # Ne pas lire les détails techniques des erreurs
    text = re.split(r"\n\s*Détail technique\s*:", text, maxsplit=1, flags=re.IGNORECASE)[0]

    # Blocs de code et code inline
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)

    # Liens markdown : [texte](url) -> texte
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Gras/italique markdown
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)

    # Titres, citations, puces
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)

    # Emojis courants / symboles décoratifs
    text = re.sub(r"[🔐🛡️🚩⚠️💡📧🔗📝✅❌]", "", text)

    # Espaces
    text = re.sub(r"\n{2,}", ". ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) > max_chars:
        shortened = text[:max_chars]
        if "." in shortened:
            shortened = shortened.rsplit(".", 1)[0] + "."
        text = shortened + " La réponse est trop longue pour être lue en intégralité. La version complète est affichée à l'écran."

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