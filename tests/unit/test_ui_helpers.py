import wave

import numpy as np

from src.ui.helpers import clean_source_name, clean_text_for_tts, normalize_transcription, save_pcm_to_wav


def test_clean_text_for_tts_removes_markdown_and_sources():
    text = "**Bonjour** [lien](https://example.com)\n\nSources :\n- doc, page 1"

    result = clean_text_for_tts(text)

    assert result == "Bonjour lien"


def test_clean_text_for_tts_removes_technical_detail():
    text = "Erreur utilisateur.\n\nDétail technique : stacktrace"

    result = clean_text_for_tts(text)

    assert result == "Erreur utilisateur."


def test_normalize_transcription_maps_fishing_to_phishing():
    assert normalize_transcription("Qu'est-ce que le fishing ?") == "Qu'est-ce que le phishing ?"


def test_normalize_transcription_maps_bad_whisper_phrase():
    assert normalize_transcription("Qu'est-ce que vous fichiez ?") == "Qu'est-ce que le phishing ?"


def test_clean_source_name_removes_markdown():
    assert clean_source_name("*messages_suspects_-_hameconnage*") == "messages_suspects_-_hameconnage"


def test_save_pcm_to_wav_creates_valid_wav(tmp_path):
    samples = np.zeros(2400, dtype=np.int16).tobytes()

    path = save_pcm_to_wav([samples], output_dir=tmp_path, sample_rate=24000)

    assert path.exists()

    with wave.open(str(path), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getframerate() == 24000