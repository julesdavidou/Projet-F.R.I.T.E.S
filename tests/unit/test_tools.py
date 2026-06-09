from tests.conftest import install_fake_retriever, reload_module


def test_format_docs_empty_returns_clear_no_result(monkeypatch):
    install_fake_retriever(monkeypatch, lambda *args, **kwargs: [])
    tools = reload_module("src.agent.tools")

    result = tools.format_docs([])

    assert "AUCUN_RESULTAT_RAG" in result


def test_search_uphf_filters_eduvpn_when_no_vpn_doc(monkeypatch):
    def fake_retrieve(query, collection_name, n_results=8):
        return [
            {
                "source": "messages_suspects_-_hameconnage",
                "page": 1,
                "text": "Courriels frauduleux et hameçonnage.",
                "distance": 12.0,
            },
            {
                "source": "l_authentification_multi-facteurs_mfa",
                "page": 0,
                "text": "Double authentification MFA.",
                "distance": 12.5,
            },
        ]

    install_fake_retriever(monkeypatch, fake_retrieve)
    tools = reload_module("src.agent.tools")

    result = tools.search_uphf.invoke({"query": "eduVPN connexion UPHF"})

    assert "AUCUN_RESULTAT_RAG" in result
    assert "messages_suspects" not in result


def test_search_uphf_keeps_eduvpn_doc(monkeypatch):
    def fake_retrieve(query, collection_name, n_results=8):
        return [
            {
                "source": "eduvpn_guide",
                "page": 2,
                "text": "Procédure de connexion eduVPN pour l'UPHF.",
                "distance": 8.0,
            }
        ]

    install_fake_retriever(monkeypatch, fake_retrieve)
    tools = reload_module("src.agent.tools")

    result = tools.search_uphf.invoke({"query": "eduVPN connexion UPHF"})

    assert "[Source: eduvpn_guide, page: 2]" in result
    assert "eduVPN" in result


def test_search_cybersec_keeps_phishing_doc(monkeypatch):
    def fake_retrieve(query, collection_name, n_results=8):
        return [
            {
                "source": "guide_phishing",
                "page": 4,
                "text": "Le phishing ou hameçonnage consiste à voler des identifiants.",
                "distance": 7.0,
            }
        ]

    install_fake_retriever(monkeypatch, fake_retrieve)
    tools = reload_module("src.agent.tools")

    result = tools.search_cybersec.invoke({"query": "comment reconnaître un phishing ?"})

    assert "[Source: guide_phishing, page: 4]" in result

def test_filter_by_distance_removes_far_docs(monkeypatch):
    install_fake_retriever(monkeypatch, lambda *args, **kwargs: [])
    tools = reload_module("src.agent.tools")

    docs = [
        {"source": "ok", "text": "phishing", "distance": 5.0},
        {"source": "too_far", "text": "phishing", "distance": 15.0},
        {"source": "no_distance", "text": "phishing"},
    ]

    result = tools.filter_by_distance(docs, max_distance=10.0)

    assert len(result) == 2
    assert result[0]["source"] == "ok"
    assert result[1]["source"] == "no_distance"


def test_filter_mfa_query_rejects_docs_without_mfa(monkeypatch):
    install_fake_retriever(monkeypatch, lambda *args, **kwargs: [])
    tools = reload_module("src.agent.tools")

    docs = [
        {
            "source": "guide_wifi",
            "text": "Sécuriser un réseau Wi-Fi avec WPA3.",
            "distance": 6.0,
        }
    ]

    result = tools.filter_query_specific_relevance(
        "Comment activer la double authentification ?",
        docs,
    )

    assert result == []


def test_filter_phishing_query_accepts_hameconnage_doc(monkeypatch):
    install_fake_retriever(monkeypatch, lambda *args, **kwargs: [])
    tools = reload_module("src.agent.tools")

    docs = [
        {
            "source": "messages_suspects_-_hameconnage",
            "text": "Un courriel suspect peut être un hameçonnage.",
            "distance": 6.0,
        }
    ]

    result = tools.filter_query_specific_relevance(
        "Comment reconnaître un mail suspect ?",
        docs,
    )

    assert result == docs