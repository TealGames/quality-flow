from typing import List, Union, Optional, Literal
import dataclasses
import os
# from vllm import LLM, SamplingParams
from tenacity import (
    retry,
    stop_after_attempt,  # type: ignore
    wait_random_exponential,  # type: ignore
)
import random
import time
from model_utils import *
from chatgpt_models import *

def model_init(model: ModelName) -> None:
    if (is_chat_gpt_model(model)):
        chatgpt_init(str(model.value))
    else:
        raise Exception(f"Attempted to initialize a model of type:'{model.value}' but no actions were specified")
    
def model_chat(model:ModelName, messages: List[Message])-> ModelChatResult:
    if (is_chat_gpt_model(model)):
        return chatgpt_chat(messages)
    else:
        raise Exception(f"Attempted to submit messages to a model:'{model.value}' with no actions defined")

def message_to_str(message: Message) -> str:
    return f"{message.role}: {message.content}"

def messages_to_str(messages: List[Message]) -> str:
    return "\n".join([message_to_str(message) for message in messages])

