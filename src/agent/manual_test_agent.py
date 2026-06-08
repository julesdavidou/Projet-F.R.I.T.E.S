from src.agent.graph import agent
from src.agent.memory import make_config

config = make_config("test-user-1")

response = agent.invoke(
    {"messages": [("user", "Comment reconnaître un mail de phishing ?")]},
    config=config,
)

print(response["messages"][-1].content)