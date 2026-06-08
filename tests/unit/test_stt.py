from types import SimpleNamespace

from src.voice import stt


class FakeWhisperModel:
    def transcribe(self, audio_path, language, vad_filter):
        return [
            SimpleNamespace(text="Bonjour"),
            SimpleNamespace(text=" le monde"),
        ], SimpleNamespace(language="fr")


def test_transcribe_joins_segments(monkeypatch):
    monkeypatch.setattr(stt, "get_model", lambda: FakeWhisperModel())

    result = stt.transcribe("fake.wav")

    assert result == "Bonjour  le monde"