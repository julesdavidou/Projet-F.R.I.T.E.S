# Interroge ChromaDB et retourne les passages les plus pertinents

import os
import chromadb
import logging
from src.rag.embeddings import embedder

logger = logging.getLogger(__name__)

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_data")
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

def retrieve(query: str, collection_name: str, n_results: int =4) -> list[dict]:
    """
    Interroge la collection ChromaDB avec la requête et retourne les passages les plus pertinents.
    Retourne une liste de dicts :
        [{"text": "...", "source": "anssi-mots_de_passe", "page": 3}, ...]
    """
    try:
        collection = chroma_client.get_collection(collection_name)
    except Exception:
        logger.error(f"Erreur lors de l'accès à la collection '{collection_name}'")
        return []
    # Calculer l'embedding de la requête et interroger ChromaDB
    query_embed = embedder.encode([query]).tolist()
    
    results = collection.query(
        query_embeddings=query_embed,
        n_results=n_results,
        include=["documents", "metadatas","distances"]
   )
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    hits = [
        {"text": doc,
        "source": meta.get("source", "?"), 
        "page": meta.get("page", -1), 
        "distance": round(dist, 4)}
        for doc, meta, dist in zip(docs, metas, dists)
    ]
    logger.debug(f"[{collection_name}] {len(hits)} hits pour la requête '{query}'")
    return hits