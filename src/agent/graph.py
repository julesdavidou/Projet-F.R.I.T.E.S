import os
from threading import RLock

from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from src.agent.guardrails import SYSTEM_PROMPT
from src.agent.memory import memory
from src.agent.tools import search_cybersec, search_uphf


OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

_MODEL_LOCK = RLock()
_ACTIVE_MODEL = OLLAMA_MODEL

tools = [search_cybersec, search_uphf]


def _make_llm(model_name: str) -> ChatOllama:
    return ChatOllama(
        model=model_name,
        base_url=OLLAMA_BASE_URL,
        temperature=0.2,
    )


def _make_agent(model: ChatOllama):
    return create_react_agent(
        model=model,
        tools=tools,
        prompt=SYSTEM_PROMPT,
        checkpointer=memory,
    )


llm = _make_llm(_ACTIVE_MODEL)
agent = _make_agent(llm)

# Alias de compatibilité avec certains essais UI
graph = agent


def get_active_model() -> str:
    return _ACTIVE_MODEL


def get_llm() -> ChatOllama:
    return llm


def get_agent():
    return agent


def set_active_model(model_name: str) -> str:
    """Change le modèle utilisé par l'agent et par la génération de titres.

    La mémoire de conversation est conservée car le checkpointer reste le même.
    """
    global _ACTIVE_MODEL, llm, agent, graph

    cleaned = (model_name or "").strip()
    if not cleaned:
        raise ValueError("Le nom du modèle ne peut pas être vide.")

    with _MODEL_LOCK:
        if cleaned == _ACTIVE_MODEL:
            return _ACTIVE_MODEL

        _ACTIVE_MODEL = cleaned
        os.environ["OLLAMA_MODEL"] = cleaned

        llm = _make_llm(cleaned)
        agent = _make_agent(llm)
        graph = agent

        return _ACTIVE_MODEL