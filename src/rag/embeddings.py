# Chargement du modele multi-lingue
from sentence_transformers import SentenceTransformer
import logging

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def load_embedder() -> SentenceTransformer:
    """
    Charge et retourne le modèle d'embedding multilingue.
    """
    try:
        logging.info(f"Modèle d'embedding '{MODEL_NAME}' chargé avec succès.")
    except Exception as e:
        logging.error(f"Erreur lors du chargement du modèle d'embedding: {e}")
        raise
    return SentenceTransformer(MODEL_NAME)

embedder = load_embedder()