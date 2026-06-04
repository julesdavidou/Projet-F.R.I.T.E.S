import chainlit as cl
import uuid
from src.agent.graph import graph

@cl.on_chat_start
async def start():

    thread_id = str(uuid.uuid4())
    cl.user_session.set("thread_id", thread_id) #donne un id à la session

    await cl.Message(
    content="Bienvenue sur L'Agent de sécurité de l'UPHF.\n Sentez-vous libre de lui demander ce que vous désirez savoir sur la cybersécurité"
    ).send() #message 

@cl.on_message
async def on_message(message: cl.Message):
    thread_id = cl.user_session.get("thread_id") #reprend l'id de session

    user_input = message.content #message de l'utilisateur

    result = await graph.ainvoke({
        "messages": [("user", user_input)]
    }, config={
        "configurable": {
            "thread_id": thread_id
        }
    })

    response = result["messages"][-1].content

    await cl.Message(content=response).send() #reponse de l'ia