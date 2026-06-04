from faster_whisper import WhisperModel

language="fr"
model = WhisperModel("small") 

#segments, info = model.transcribe(audio_path)