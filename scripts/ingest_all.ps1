# scripts/ingest_all.ps1
# Régénère toute la base ChromaDB depuis zéro
# Usage : .\scripts\ingest_all.ps1

Write-Host "════════════════════════════════════════"
Write-Host "  RÉINGESTION COMPLÈTE DE LA BASE RAG"
Write-Host "════════════════════════════════════════"

# ── Suppression de l'ancienne base ───────────────────────────────────────
if (Test-Path "./chroma_data") {
    Write-Host "[1/3] Suppression de l'ancienne base chroma_data/..."
    Remove-Item -Recurse -Force "./chroma_data"
    Write-Host "      OK Ancienne base supprimée."
} else {
    Write-Host "[1/3] Aucune base existante à supprimer."
}

# ── Vérification des dossiers sources ────────────────────────────────────
Write-Host "[2/3] Vérification des dossiers sources..."

$cybersecPdfs = Get-ChildItem -Path "./data/knowledge/cybersec/" -Filter "*.pdf" -ErrorAction SilentlyContinue
if ($cybersecPdfs.Count -eq 0) {
    Write-Host "      ATTENTION Aucun PDF dans data/knowledge/cybersec/ — collection cybersec_fr sera vide."
} else {
    Write-Host "      OK $($cybersecPdfs.Count) PDF(s) cybersec trouvés."
}

$uphfPdfs = Get-ChildItem -Path "./data/knowledge/uphf/" -Filter "*.pdf" -ErrorAction SilentlyContinue
if ($uphfPdfs.Count -eq 0) {
    Write-Host "      ATTENTION Aucun PDF dans data/knowledge/uphf/ — collection uphf_docs sera vide."
} else {
    Write-Host "      OK $($uphfPdfs.Count) PDF(s) UPHF trouvés."
}

# ── Lancement de l'ingestion ──────────────────────────────────────────────
Write-Host "[3/3] Lancement de l'ingestion..."
python -m src.rag.ingest

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "════════════════════════════════════════"
    Write-Host "  OK Réingestion terminée avec succès."
    Write-Host "════════════════════════════════════════"
} else {
    Write-Host ""
    Write-Host "  ERREUR Une erreur est survenue durant l'ingestion."
    exit 1
}