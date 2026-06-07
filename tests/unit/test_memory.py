from src.agent.memory import make_config


def test_make_config_sets_thread_id():
    assert make_config("abc") == {"configurable": {"thread_id": "abc"}}