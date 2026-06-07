from langchain_core.tools import tool

from src.rag.retriever import retrieve


def format_docs(docs: list[dict]) -> str:
    if not docs:
        return "AUCUN_RESULTAT_RAG: aucun document pertinent trouvé dans cette collection."

    return "\n---\n".join(
        f"[Source: {d.get('source', 'inconnue')}, page: {d.get('page', '?')}] {d.get('text', '')}"
        for d in docs
    )


@tool
def search_cybersec(query: str) -> str:
    """Recherche dans la base de connaissances cybersécurité générale."""
    print(f"[RAG] search_cybersec appelé avec : {query}", flush=True)

    docs = retrieve(
        query,
        collection_name="cybersec_fr",
        n_results=4,
    )

    print(f"[RAG] cybersec résultats : {len(docs)}", flush=True)

    return format_docs(docs)


@tool
def search_uphf(query: str) -> str:
    """Recherche dans la documentation sécurité UPHF, DNum, eduVPN, MFA et messagerie."""
    print(f"[RAG] search_uphf appelé avec : {query}", flush=True)

    docs = retrieve(
        query,
        collection_name="uphf_docs",
        n_results=4,
    )

    print(f"[RAG] uphf résultats : {len(docs)}", flush=True)

    return format_docs(docs)