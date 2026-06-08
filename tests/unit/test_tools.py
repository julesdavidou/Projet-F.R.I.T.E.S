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