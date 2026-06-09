import re

from src.agent import graph as agent_graph
from src.agent.guardrails import is_potentially_dangerous, safe_fallback
from src.agent.memory import make_config


SOURCE_PATTERN = re.compile(
    r"\[Source:\s*(?P<source>[^,\]]+)(?:,\s*page:\s*(?P<page>[^\]]+))?\]"
)


def _extract_last_content(result: dict) -> str:
    messages = result.get("messages", [])

    if not messages:
        return "Je n'ai pas réussi à générer de réponse."

    last_message = messages[-1]

    if hasattr(last_message, "content"):
        return last_message.content

    return str(last_message)


def _extract_sources_from_tool_messages(result: dict) -> list[str]:
    sources = []

    for message in result.get("messages", []):
        content = getattr(message, "content", "")

        if not isinstance(content, str):
            continue

        for match in SOURCE_PATTERN.finditer(content):
            source = match.group("source").strip()
            page = match.group("page")

            if page:
                citation = f"{source}, page {page.strip()}"
            else:
                citation = source

            if citation not in sources:
                sources.append(citation)

    return sources


def _append_sources(answer: str, sources: list[str]) -> str:
    if not sources:
        return answer

    if "Sources" in answer or "Source" in answer:
        return answer

    formatted_sources = "\n".join(f"- {source}" for source in sources)

    return f"{answer}\n\nSources :\n{formatted_sources}"


async def ask_agent(user_input: str, thread_id: str) -> str:
    user_input = user_input.strip()

    if not user_input:
        return "Pose-moi une question sur la cybersécurité ou les services numériques de l'UPHF."

    if is_potentially_dangerous(user_input):
        return safe_fallback()

    try:
        result = await agent_graph.get_agent().ainvoke(
            {"messages": [("user", user_input)]},
            config=make_config(thread_id),
        )
    except Exception as exc:
        return (
            "Je n'arrive pas à interroger correctement le modèle local Ollama. "
            "Vérifie qu'Ollama est lancé, que le modèle configuré est téléchargé, "
            "et qu'il n'est pas trop lourd pour la mémoire disponible.\n\n"
            f"Modèle actif : {agent_graph.get_active_model()}\n"
            f"Détail technique : {exc}"
        )

    answer = _extract_last_content(result)

    if is_potentially_dangerous(answer):
        return safe_fallback()

    sources = _extract_sources_from_tool_messages(result)
    answer = _append_sources(answer, sources)

    return answer