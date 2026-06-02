def test_agent_imports():
    from src.agent.graph import agent

    assert agent is not None


def test_tools_import():
    from src.agent.tools import search_cybersec, search_uphf

    assert search_cybersec is not None
    assert search_uphf is not None


def test_memory_config():
    from src.agent.memory import make_config

    config = make_config("test-user-1")

    assert config == {"configurable": {"thread_id": "test-user-1"}}