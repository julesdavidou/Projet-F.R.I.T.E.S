# ----------------------------------------------------
#           CECI EST UN PROGRAMME TEMPORAIRE
#             UTILISE POUR TESTER LA GUI
# ----------------------------------------------------

# src/agent/graph.py
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

# Ceci est un faux agent (bouchon) pour tester Chainlit
# Il renverra toujours un écho de ce que l'utilisateur a dit.
def mock_agent_logic(state: dict) -> dict:
    user_messages = state.get("messages", [])
    if not user_messages:
        return {"messages": [AIMessage(content="Erreur: Aucun message reçu.")]}
    
    last_user_input = user_messages[-1][1] if isinstance(user_messages[-1], tuple) else user_messages[-1].content
    
    # Réponse bidon pour tester l'interface
    fake_response = f"Ceci est une réponse temporaire du système. Vous avez dit : '{last_user_input}'"
    
    return {"messages": [AIMessage(content=fake_response)]}

# On simule l'objet "graph" attendu par app.py
graph = RunnableLambda(mock_agent_logic)