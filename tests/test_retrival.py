# test/test_retrieval.py
# Teste la pertinence des résultats RAG sur des questions types

from src.rag.retriever import retrieve

# ── Questions de test ─────────────────────────────────────────────────────
TESTS = [
    # (question, collection)
    ("Quels sont les critères d'un bon mot de passe ?",      "cybersec_fr"),
    ("Comment signaler un phishing ?",                        "cybersec_fr"),
    ("Quelles sont les bonnes pratiques Wi-Fi ?",             "cybersec_fr"),
    ("Comment activer le 2FA à l'UPHF ?",                    "uphf_docs"),
    ("Où trouver le guide eduVPN de l'UPHF ?",               "uphf_docs"),
    ("Quels sont les usages interdits sur le réseau UPHF ?", "uphf_docs"),
]

# ── Seuil d'alerte (distance L2 ChromaDB) ────────────────────────────
# < 6.5  → très pertinent 
# 6.5-9.0 → pertinent mais à vérifier 
# > 9.0  → probablement hors sujet 
THRESHOLD_OK   = 9.5
THRESHOLD_WARN = 12.0


def label(distance: float) -> str:
    if distance < THRESHOLD_OK:
        return "✅ "
    elif distance < THRESHOLD_WARN:
        return "⚠️ "
    else:
        return "❌"


def run_tests():
    print("\n" + "═" * 70)
    print("  TEST DE PERTINENCE RAG")
    print("═" * 70)

    for question, collection in TESTS:
        print(f"\n Question : {question}")
        print(f"   Collection : {collection}")
        print("─" * 70)

        hits = retrieve(question, collection, n_results=3)

        if not hits:
            print("    Aucun résultat — collection vide ou introuvable.")
            continue

        for i, hit in enumerate(hits, 1):
            icon = label(hit["distance"])
            print(f"   {icon} Résultat {i} | source={hit['source']} | page={hit['page']} | dist={hit['distance']}")
            # Affiche les 200 premiers caractères du chunk
            preview = hit["text"].replace("\n", " ").strip()[:200]
            print(f"      → {preview}…")

    print("\n" + "═" * 70)
    print("  Légende : ✅ < 9.5  |  ⚠️  9.5-12.0  |  ❌ > 12.0")
    print("═" * 70 + "\n")


if __name__ == "__main__":
    run_tests()