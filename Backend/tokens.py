from typing import List
from mistral_common.protocol.instruct.messages import (
    AssistantMessage,
    UserMessage,
    SystemMessage
)
from mistral_common.tokens.tokenizers.mistral import MistralTokenizer
from mistral_common.protocol.instruct.request import ChatCompletionRequest
from llama_index.core.llms import ChatMessage

tokenizer_v3 = MistralTokenizer.v3()


def get_token_count(history: List[ChatMessage]) -> int:
    messages = []

    for msg in history:
        if msg.role == "system":
            messages.append(SystemMessage(content=msg.content))
        elif msg.role == "user":
            messages.append(UserMessage(content=msg.content))
        elif msg.role == "assistant":
            messages.append(AssistantMessage(content=msg.content))

    request =  ChatCompletionRequest(
        messages=messages,
        model="mistral-small-latest",
    )

    tokenized = tokenizer_v3.encode_chat_completion(request)

    return len(tokenized.tokens)