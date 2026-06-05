import chainlit as cl
import numpy as np
import wave
import uuid
from pathlib import Path
#from src.agent.graph import graph

@cl.on_chat_start
async def start():

    thread_id = str(uuid.uuid4())
    cl.user_session.set("thread_id", thread_id) #donne un id à la session

    await cl.Message(
        content="Bienvenue sur L'Agent de sécurité de l'UPHF.\n Sentez-vous libre de lui demander ce que vous désirez savoir sur la cybersécurité"
    ).send() #message 
"""
@cl.on_message
async def on_message(message: cl.Message):
    thread_id = cl.user_session.get("thread_id") #reprend l'id de session

    user_input = message.content #message de l'utilisateur

    result = await graph.ainvoke({
        "messages": [("user", user_input)]
    }, config={
        "configurable": {
            "thread_id": thread_id
        }
    })

    response = result["messages"][-1].content

    await cl.Message(content=response).send() #reponse de l'ia
"""
@cl.on_chat_start
async def start():
    cl.user_session.set("audio_buffer", [])



@cl.on_audio_chunk
async def on_audio_chunk(chunk):
    buffer = cl.user_session.get("audio_buffer")
    buffer.append(chunk.data)

    cl.user_session.set("audio_buffer", buffer)

def save_pcm_to_wav(pcm_bytes: list[bytes], sample_rate=24000):

    audio_dir = Path("tmp/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)

    file_path = audio_dir / f"{uuid.uuid4()}.wav"

    # concat chunks
    raw_audio = b"".join(pcm_bytes)

    # convert bytes -> int16 array
    audio_array = np.frombuffer(raw_audio, dtype=np.int16)

    # write wav
    with wave.open(str(file_path), "wb") as wf:
        wf.setnchannels(1)      # mono
        wf.setsampwidth(2)      # int16 = 2 bytes
        wf.setframerate(sample_rate)
        wf.writeframes(audio_array.tobytes())

    return file_path

@cl.on_audio_end
async def on_audio_end():

    buffer = cl.user_session.get("audio_buffer")

    wav_path = save_pcm_to_wav(buffer)

    print("WAV généré :", wav_path)

    text = transcribe(str(wav_path))

    print("TRANSCRIPTION :", text)