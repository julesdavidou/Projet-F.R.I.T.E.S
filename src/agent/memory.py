from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()


def make_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}