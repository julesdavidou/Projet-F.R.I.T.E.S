from langchain_core.tools import tool

from src.rag.retriever import retrieve

# Au-dessus de 10.0, le document est considéré comme hors sujet par rapport à la question.
DISTANCE_MAX = 10.0


@tool
def search_cybersec(query: str) -> str:
    """Recherche dans la base de connaissances cybersécurité générale."""
    print(f"[RAG] search_cybersec appelé avec : {query}", flush=True)

    docs = retrieve(
        query,
        collection_name="cybersec_fr",
        n_results=8,
    )

    # Remplacement de max_distance=None par notre limite
    docs = filter_by_distance(docs, max_distance=DISTANCE_MAX)
    docs = filter_query_specific_relevance(query, docs)
    docs = docs[:4]

    print(f"[RAG] cybersec résultats pertinents : {len(docs)}", flush=True)

    return format_docs(docs)


@tool
def search_uphf(query: str) -> str:
    """Recherche dans la documentation sécurité UPHF, DNum, eduVPN, MFA et messagerie."""
    print(f"[RAG] search_uphf appelé avec : {query}", flush=True)

    docs = retrieve(
        query,
        collection_name="uphf_docs",
        n_results=8,
    )

    # Remplacement de max_distance=None par notre limite
    docs = filter_by_distance(docs, max_distance=DISTANCE_MAX) # max_distance=None avant, pas de filtrage dcp
    docs = filter_query_specific_relevance(query, docs)
    docs = docs[:4]

    print(f"[RAG] uphf résultats pertinents : {len(docs)}", flush=True)

    return format_docs(docs)


def doc_to_searchable_text(doc: dict) -> str:
    return f"{doc.get('source', '')} {doc.get('text', '')}".lower()


def query_mentions_any(query: str, terms: list[str]) -> bool:
    q = query.lower()
    return any(term in q for term in terms)


def docs_contain_any(docs: list[dict], terms: list[str]) -> bool:
    joined = "\n".join(doc_to_searchable_text(doc) for doc in docs)
    return any(term in joined for term in terms)


def filter_query_specific_relevance(query: str, docs: list[dict]) -> list[dict]:
    """Évite de renvoyer des documents hors sujet.

    Exemple : si la question parle d'eduVPN, on refuse des docs MFA/phishing
    qui ne mentionnent jamais eduVPN ou VPN.
    """

    if query_mentions_any(query, ["eduvpn", "vpn"]):
        if not docs_contain_any(docs, ["eduvpn", "vpn"]):
            return []

    if query_mentions_any(query, ["mfa", "multi-facteurs", "double authentification"]):
        if not docs_contain_any(docs, ["mfa", "multi-facteurs", "double authentification"]):
            return []

    if query_mentions_any(query, ["phishing", "hameçonnage", "mail suspect", "courriel suspect"]):
        if not docs_contain_any(docs, ["phishing", "hameçonnage", "courriel", "mail suspect"]):
            return []

    return docs


def filter_by_distance(docs: list[dict], max_distance: float | None = None) -> list[dict]:
    if max_distance is None:
        return docs

    filtered = []

    for doc in docs:
        distance = doc.get("distance")

        if distance is None:
            filtered.append(doc)
            continue

        if distance <= max_distance:
            filtered.append(doc)

    return filtered


def format_docs(docs: list[dict]) -> str:
    if not docs:
        return (
            "AUCUN_RESULTAT_RAG: aucun document suffisamment pertinent "
            "n'a été trouvé dans cette collection."
        )

    return "\n---\n".join(
        f"[Source: {d.get('source', 'inconnue')}, page: {d.get('page', '?')}] "
        f"{d.get('text', '')}"
        for d in docs
    )