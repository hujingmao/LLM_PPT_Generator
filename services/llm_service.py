"""大模型调用封装。"""

from langchain_core.messages import HumanMessage, SystemMessage

from model_factory import build_chat_model


class LLMService:
    def __init__(self):
        self.chat_model = build_chat_model()

    def invoke(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = self.chat_model.invoke(messages)
        return getattr(response, "content", str(response))

