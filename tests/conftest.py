import importlib
import sys
import types
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class FakeAgent:
    def __init__(self, result=None, exc=None):
        self.result = result or {"messages": []}
        self.exc = exc
        self.calls = []

    async def ainvoke(self, payload, config=None):
        self.calls.append((payload, config))
        if self.exc:
            raise self.exc
        return self.result


def reload_module(module_name: str):
    if module_name in sys.modules:
        return importlib.reload(sys.modules[module_name])
    return importlib.import_module(module_name)


def install_fake_graph(monkeypatch, fake_agent):
    fake_graph = types.ModuleType("src.agent.graph")
    fake_graph.agent = fake_agent
    fake_graph.graph = fake_agent
    monkeypatch.setitem(sys.modules, "src.agent.graph", fake_graph)


def install_fake_retriever(monkeypatch, fake_retrieve):
    fake_module = types.ModuleType("src.rag.retriever")
    fake_module.retrieve = fake_retrieve
    monkeypatch.setitem(sys.modules, "src.rag.retriever", fake_module)
