import dataclasses
from typing import Literal, Union, List
from enum import Enum

MessageRole = Literal["system", "user", "assistant"]

@dataclasses.dataclass()
class Message():
    role: MessageRole
    content: str

def message_length_check(tokenizer, messages, max_len) -> list[Message]:
    original_messages = messages
    new_messages = messages[:1]
    total_msg_len = len(tokenizer.tokenize(messages[0].content))
    rest_messages = []
    for msg in reversed(messages[1:]):
        msg_len = len(tokenizer.tokenize(msg.content))
        if msg_len + total_msg_len < max_len:
            rest_messages = [msg] + rest_messages
            total_msg_len += msg_len
        else:
            break
    messages = new_messages + rest_messages
    return messages

class ModelName(Enum):
    ChatGPT = 0
    Gemini = 1
    Claude = 2

def get_model_name(name: str) -> ModelName:
    return ModelName[name]

class ModelChatResult:
    def __init__(self, messages:List[Message], output:str, input_tokens:int, output_tokens:int):
        self.messages= messages
        self.output= output
        self.input_tokens= input_tokens
        self.output_tokens= output_tokens



