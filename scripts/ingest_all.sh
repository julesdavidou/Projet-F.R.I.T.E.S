#!/bin/bash
# scripts/ingest_all.sh
# Régénère toute la base ChromaDB depuis zéro
# Usage : bash scripts/ingest_all.sh

set -e  # Arrête le script si une commande échoue

echo "----------------------------------------"
echo "  REINGESTION COMPLETE DE LA BASE RAG"
echo "----------------------------------------"

# ── Suppression de l'ancienne base ───────────────────────────────────────
if [ -d "./chroma_data" ]; then
    echo "[1/3] Suppression de l'ancienne base chroma_data/..."
    rm -rf ./chroma_data
    echo "      Ancienne base supprimee."
else
    echo "[1/3] Aucune base existante a supprimer."
fi

# ── Vérification des dossiers sources ────────────────────────────────────
echo "[2/3] Verification des dossiers sources..."

if [ -z "$(ls -A ./data/knowledge/cybersec/*.pdf 2>/dev/null)" ]; then
    echo "      Aucun PDF dans data/knowledge/cybersec/ — collection cybersec_fr sera vide."
else
    echo "      PDF cybersec trouves."
fi

if [ -z "$(ls -A ./data/knowledge/uphf/*.pdf 2>/dev/null)" ]; then
    echo "      Aucun PDF dans data/knowledge/uphf/ — collection uphf_docs sera vide."
else
    echo "      PDF UPHF trouves."
fi

# ── Lancement de l'ingestion ──────────────────────────────────────────────
echo "[3/3] Lancement de l'ingestion..."
python -m src.rag.ingest

echo ""
echo "----------------------------------------"
echo "  Réingestion terminee."
echo "----------------------------------------"