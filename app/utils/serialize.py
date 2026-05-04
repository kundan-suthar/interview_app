from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

def serialize_messages(messages: list) -> list:
    serialized = []
    for m in messages:
        if isinstance(m, SystemMessage):
            continue  # skip system prompts
        elif isinstance(m, HumanMessage):
            serialized.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            serialized.append({"role": "assistant", "content": m.content})
    return serialized