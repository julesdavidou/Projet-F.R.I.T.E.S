# Lit les PDF, découpe en chunks, calcule les embeddings, stocke dans ChromaDB

import os
import logging
import chromadb
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .embeddings import embedder

logger = logging.getLogger(__name__)

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_data")
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

# Paramètres de découpage
CHUNK_SIZE = 600 # nombre de token par chunk
CHUNK_OVERLAP = 80 # chevauchement entre les chunks

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE, 
    chunk_overlap=CHUNK_OVERLAP
)

def ingest_pdf(path: str, source_tag: str, collection_name: str) -> int:
    """
    Ingère un PDF : lit, découpe en chunks, calcule les embeddings, stocke dans ChromaDB.
    Puis retourne le nombre de chunks ingérés.
    """

    collection = chroma_client.get_or_create_collection(collection_name)

    # Charger le PDF
    try:
        docs = PyPDFLoader(path).load()
        chuncks = splitter.split_documents(docs)

        if not chuncks:
            logger.warning(f"Aucun chunk généré pour le PDF '{path}'.")
            return 0
        # Calculer les embeddings
        texts = [chunk.page_content for chunk in chuncks]
        embeds = embedder.encode(texts, show_progress_bar=True).tolist()
        ids = [f"{source_tag}_{i}" for i in range(len(chuncks))]
        metas = [
            {"source": source_tag, "page": chunk.metadata.get("page",0)}
            for chunk in chuncks
        ]

        # Stocker dans ChromaDB
        collection.add(
            ids=ids,
            embeddings=embeds,
            metadatas=metas,
            documents=texts
        )
        logger.info(f"{len(chuncks)} chunks ingérés pour le PDF '{path}' dans la collection '{collection_name}'.")
        return len(chuncks)
    
    except Exception as e:
        logger.error(f"Erreur lors de l'ingestion du PDF '{path}': {e}")
        return 0
    
def ingest_folder(folder:str, collection_name:str) -> None:
    """
    Ingère tous les PDF d'un dossier dans une collection ChromaDB.
    """
    for filename in os.listdir(folder):
        if filename.lower().endswith(".pdf"):
            path = os.path.join(folder, filename)
            source_tag = filename[:-4] # nom du fichier sans extension
            ingest_pdf(
                path,
                source_tag, 
                collection_name
            )