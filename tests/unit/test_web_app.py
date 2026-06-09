import importlib
import sys
import types

from fastapi.testclient import TestClient


def load_web_app_with_fakes(monkeypatch):
    fake_graph = types.ModuleType("src.agent.graph")
    fake_graph.get_active_model = lambda: "fake-model"
    fake_graph.set_active_model = lambda model: model

    class FakeLLM:
        async def ainvoke(self, prompt):
            return types.SimpleNamespace(content="Titre court")

    fake_graph.get_llm = lambda: FakeLLM()

    fake_runner = types.ModuleType("src.agent.runner")

    async def fake_ask_agent(user_input: str, thread_id: str) -> str:
        return (
            "Réponse de test.\n\n"
            "Sources :\n"
            "- messages_suspects_-_hameconnage, page 1"
        )

    fake_runner.ask_agent = fake_ask_agent

    monkeypatch.setitem(sys.modules, "src.agent.graph", fake_graph)
    monkeypatch.setitem(sys.modules, "src.agent.runner", fake_runner)

    if "src.ui.web_app" in sys.modules:
        return importlib.reload(sys.modules["src.ui.web_app"])

    return importlib.import_module("src.ui.web_app")


def test_health_endpoint(monkeypatch):
    web_app = load_web_app_with_fakes(monkeypatch)
    client = TestClient(web_app.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_endpoint_returns_sources(monkeypatch):
    web_app = load_web_app_with_fakes(monkeypatch)
    client = TestClient(web_app.app)

    response = client.post(
        "/api/chat",
        json={"conversation_id": "test-thread", "message": "Comment signaler un phishing ?"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["content"].startswith("Réponse de test")
    assert data["conversation_id"] == "test-thread"
    assert len(data["steps"]) >= 2