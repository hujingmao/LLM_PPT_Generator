"""大模型调用封装。

此处把 LangChain 的消息构造和模型调用收敛到一个小服务里。
其他业务模块只关心 system_prompt/user_prompt，不关心底层模型对象。
"""

from langchain_core.messages import HumanMessage, SystemMessage

from model_factory import build_chat_model


class LLMService:
    """统一的大模型调用入口。"""

    def __init__(self):
        # build_chat_model 会根据 config_data 中的 provider 决定使用哪一种模型。
        self.chat_model = build_chat_model()

    def invoke(self, system_prompt: str, user_prompt: str) -> str:
        """调用聊天模型并返回纯文本内容。"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = self.chat_model.invoke(messages)
        return getattr(response, "content", str(response))
