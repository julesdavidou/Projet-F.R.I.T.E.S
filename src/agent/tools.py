from langchain_core.tools import tool

try:
    from src.rag.retriever import retrieve
except ImportError:
    retrieve = None


@tool
def search_cybersec(query: str) -> str:
    """Recherche dans la base cybersécurité : ANSSI, CNIL, cybermalveillance."""
    if retrieve is None:
        return "RAG indisponible : src.rag.retriever.retrieve n'est pas encore prêt."

    try:
        docs = retrieve(query=query, collection_name="cybersec_fr", n_results=4)
    except Exception as exc:
        return f"Erreur RAG temporaire : {exc}"

    if not docs:
        return "Aucun document cybersécurité pertinent trouvé."

    return "\n---\n".join(
        f"[Source: {d.get('source', 'inconnue')}] {d.get('text', '')}"
        for d in docs
    )


@tool
def search_uphf(query: str) -> str:
    """Recherche dans la documentation sécurité UPHF / DNum."""
    if retrieve is None:
        return "RAG indisponible : src.rag.retriever.retrieve n'est pas encore prêt."

    try:
        docs = retrieve(query=query, collection_name="uphf_docs", n_results=4)
    except Exception as exc:
        return f"Erreur RAG temporaire : {exc}"

    if not docs:
        return "Aucun document UPHF pertinent trouvé."

    return "\n---\n".join(
        f"[Source: {d.get('source', 'inconnue')}] {d.get('text', '')}"
        for d in docs
    )