# Tests unitaires pour le pipeline RAG
# Usage : pytest tests/unit/test_rag.py -v

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from src.rag.ingest import ingest_pdf, chroma_client
from src.rag.retriever import retrieve

# ── Constantes ────────────────────────────────────────────────────────────
CYBERSEC_COLLECTION = "cybersec_fr"
UPHF_COLLECTION     = "uphf_docs"
TEST_QUERY          = "mot de passe sécurisé"


# ── Tests d'ingestion ─────────────────────────────────────────────────────

class TestIngestion:

    def test_collections_exist(self):
        """Les deux collections doivent exister dans ChromaDB."""
        collections = [c.name for c in chroma_client.list_collections()]
        assert CYBERSEC_COLLECTION in collections, \
            f"Collection '{CYBERSEC_COLLECTION}' introuvable — lancez ingest.py"
        assert UPHF_COLLECTION in collections, \
            f"Collection '{UPHF_COLLECTION}' introuvable — lancez ingest.py"

    def test_cybersec_collection_not_empty(self):
        """La collection cybersec_fr doit contenir des chunks."""
        count = chroma_client.get_collection(CYBERSEC_COLLECTION).count()
        assert count > 0, "cybersec_fr est vide — vérifiez data/knowledge/cybersec/"

    def test_uphf_collection_not_empty(self):
        """La collection uphf_docs doit contenir des chunks."""
        count = chroma_client.get_collection(UPHF_COLLECTION).count()
        assert count > 0, "uphf_docs est vide — vérifiez data/knowledge/uphf/"


# ── Tests du retriever ────────────────────────────────────────────────────

class TestRetriever:

    def test_retrieve_returns_results(self):
        """retrieve() doit retourner une liste non vide."""
        hits = retrieve(TEST_QUERY, CYBERSEC_COLLECTION)
        assert len(hits) > 0, "Aucun résultat retourné"

    def test_retrieve_default_n_results(self):
        """retrieve() doit retourner 4 résultats par défaut."""
        hits = retrieve(TEST_QUERY, CYBERSEC_COLLECTION)
        assert len(hits) == 4

    def test_retrieve_custom_n_results(self):
        """retrieve() doit respecter le paramètre n_results."""
        hits = retrieve(TEST_QUERY, CYBERSEC_COLLECTION, n_results=2)
        assert len(hits) == 2

    def test_retrieve_hit_has_required_keys(self):
        """Chaque résultat doit contenir les clés : text, source, page, distance."""
        hits = retrieve(TEST_QUERY, CYBERSEC_COLLECTION, n_results=1)
        hit = hits[0]
        for key in ("text", "source", "page", "distance"):
            assert key in hit, f"Clé manquante dans le résultat : '{key}'"

    def test_retrieve_text_not_empty(self):
        """Le champ 'text' de chaque résultat ne doit pas être vide."""
        hits = retrieve(TEST_QUERY, CYBERSEC_COLLECTION)
        for hit in hits:
            assert hit["text"].strip() != "", "Un chunk retourné est vide"

    def test_retrieve_source_not_empty(self):
        """Le champ 'source' doit être renseigné (non vide, non '?')."""
        hits = retrieve(TEST_QUERY, CYBERSEC_COLLECTION)
        for hit in hits:
            assert hit["source"] not in ("", "?"), \
                "Un chunk retourné n'a pas de source renseignée"

    def test_retrieve_distance_is_positive(self):
        """La distance doit être un nombre positif."""
        hits = retrieve(TEST_QUERY, CYBERSEC_COLLECTION)
        for hit in hits:
            assert isinstance(hit["distance"], float)
            assert hit["distance"] >= 0

    def test_retrieve_results_ordered_by_distance(self):
        """Les résultats doivent être triés par distance croissante."""
        hits = retrieve(TEST_QUERY, CYBERSEC_COLLECTION, n_results=4)
        distances = [h["distance"] for h in hits]
        assert distances == sorted(distances), \
            "Les résultats ne sont pas triés par distance croissante"

    def test_retrieve_unknown_collection_returns_empty(self):
        """retrieve() sur une collection inexistante doit retourner []."""
        hits = retrieve(TEST_QUERY, "collection_inexistante")
        assert hits == [], \
            "Une collection inexistante doit retourner une liste vide, pas une exception"

    def test_retrieve_uphf_collection(self):
        """retrieve() doit aussi fonctionner sur la collection uphf_docs."""
        hits = retrieve("authentification UPHF", UPHF_COLLECTION)
        assert len(hits) > 0