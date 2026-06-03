# Lit les PDF, découpe en chunks, calcule les embeddings, stocke dans ChromaDB

import os
import logging
import chromadb
from langchain.community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
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