import os

import pytest

from src.agent.runner import ask_agent


@pytest.mark.ollama
@pytest.mark.asyncio
async def test_agent_smoke_with_ollama():
    if not os.getenv("RUN_OLLAMA_TESTS"):
        pytest.skip("Ollama tests disabled. Set RUN_OLLAMA_TESTS=1 to run.")

    result = await ask_agent("Comment reconnaître un mail de phishing ?", "test-thread")

    assert result
    assert "phishing" in result.lower() or "hameçonnage" in result.lower()