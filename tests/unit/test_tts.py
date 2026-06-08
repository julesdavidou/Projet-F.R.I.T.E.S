import subprocess
from pathlib import Path

import pytest

from src.voice import tts


def test_is_tts_available_false_without_piper(monkeypatch):
    monkeypatch.setattr(tts.shutil, "which", lambda _: None)

    assert not tts.is_tts_available()


def test_synthesize_raises_when_piper_missing(monkeypatch):
    monkeypatch.setattr(tts.shutil, "which", lambda _: None)

    with pytest.raises(FileNotFoundError):
        tts.synthesize("Bonjour")


def test_synthesize_generates_file_when_piper_and_models_exist(monkeypatch, tmp_path):
    model = tmp_path / "voice.onnx"
    config = tmp_path / "voice.onnx.json"
    model.write_text("fake model")
    config.write_text("fake config")

    monkeypatch.setattr(tts, "MODEL_PATH", model)
    monkeypatch.setattr(tts, "CONFIG_PATH", config)
    monkeypatch.setattr(tts, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(tts.shutil, "which", lambda _: "piper")

    def fake_run(args, input, text, check):
        output_index = args.index("--output_file") + 1
        output_path = Path(args[output_index])
        output_path.write_bytes(b"fake wav")

    monkeypatch.setattr(subprocess, "run", fake_run)

    path = tts.synthesize("Bonjour")

    assert path.exists()
    assert path.stat().st_size > 0