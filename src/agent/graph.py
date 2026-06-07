import os

from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from src.agent.guardrails import SYSTEM_PROMPT
from src.agent.memory import memory
from src.agent.tools import search_cybersec, search_uphf


OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
#OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi4-mini") ##si pb
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434") ##http://localhost:11434

llm = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0.2,
)

tools = [search_cybersec, search_uphf]

agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=SYSTEM_PROMPT, #si fonctionne pas tester : state_modifier
    checkpointer=memory,
)

# Alias de compatibilité avec certains essais UI
graph = agent