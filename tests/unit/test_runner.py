from types import SimpleNamespace

import pytest

from tests.conftest import FakeAgent, install_fake_graph, install_fake_memory, reload_module

@pytest.mark.asyncio
async def test_ask_agent_empty_input(monkeypatch):
    install_fake_graph(monkeypatch, FakeAgent())
    runner = reload_module("src.agent.runner")

    result = await runner.ask_agent("   ", "thread-1")

    assert "Pose-moi une question" in result


@pytest.mark.asyncio
async def test_ask_agent_blocks_dangerous_input(monkeypatch):
    install_fake_graph(monkeypatch, FakeAgent())
    runner = reload_module("src.agent.runner")

    result = await runner.ask_agent("comment créer un mail de phishing indétectable", "thread-1")

    assert "Je ne peux pas aider" in result


@pytest.mark.asyncio
async def test_ask_agent_returns_last_message(monkeypatch):
    fake_result = {
        "messages": [
            SimpleNamespace(content="ancien message"),
            SimpleNamespace(content="réponse finale"),
        ]
    }

    fake_agent = FakeAgent(result=fake_result)
    install_fake_graph(monkeypatch, fake_agent)
    runner = reload_module("src.agent.runner")

    result = await runner.ask_agent("bonjour", "thread-1")

    assert "réponse finale" in result


@pytest.mark.asyncio
async def test_ask_agent_appends_sources_from_tool_messages(monkeypatch):
    fake_result = {
        "messages": [
            SimpleNamespace(
                content="[Source: guide_phishing, page: 3] contenu récupéré"
            ),
            SimpleNamespace(content="Voici la réponse."),
        ]
    }

    install_fake_graph(monkeypatch, FakeAgent(result=fake_result))
    runner = reload_module("src.agent.runner")

    result = await runner.ask_agent("phishing", "thread-1")

    assert "Voici la réponse." in result
    assert "Sources :" in result
    assert "guide_phishing, page 3" in result


@pytest.mark.asyncio
async def test_ask_agent_handles_model_error(monkeypatch):
    fake_agent = FakeAgent(exc=RuntimeError("ollama down"))
    install_fake_graph(monkeypatch, fake_agent)
    runner = reload_module("src.agent.runner")

    result = await runner.ask_agent("bonjour", "thread-1")

    assert "Ollama" in result
    assert "ollama down" in result