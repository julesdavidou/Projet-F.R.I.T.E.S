import pytest

from src.agent.tools import search_cybersec, search_uphf


@pytest.mark.integration
def test_phishing_returns_relevant_cybersec_source():
    result = search_cybersec.invoke({"query": "Comment reconnaître un mail de phishing ?"})

    assert "AUCUN_RESULTAT_RAG" not in result
    assert "phishing" in result.lower() or "hameçonnage" in result.lower()


@pytest.mark.integration
def test_eduvpn_returns_no_result_until_doc_is_indexed():
    result = search_uphf.invoke({"query": "eduVPN connexion UPHF"})

    assert "AUCUN_RESULTAT_RAG" in result


@pytest.mark.integration
def test_uphf_phishing_returns_hameconnage_source():
    result = search_uphf.invoke({"query": "Que faire à l'UPHF si je reçois un mail suspect ?"})

    assert "messages_suspects" in result