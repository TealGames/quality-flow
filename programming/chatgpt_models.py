import os
import openai
from openai import OpenAI
from transformers import GPT2Tokenizer, AutoTokenizer
from model_utils import *
from typing import Union

MAX_TOKENS:int= 1024
DEFAULT_TEMPERATURE:float= 0.2
MESSAGE_CHOICE_INDEX: int =0
API_KEY_VAR_NAME: str= "OPENAI_API_KEY"

class ChatGPTModel:
    def __init__(self, name:str):
        self.name= name
        self.tokenizer=GPT2Tokenizer.from_pretrained("gpt2")
        self.client = OpenAI()

Model: ChatGPTModel | None = None

def chatgpt_init(model_name:str):
    global Model
    openai.api_key = os.getenv(API_KEY_VAR_NAME)
    Model= ChatGPTModel(model_name)

def chatgpt_chat(messages: List[Message]) -> ModelChatResult:
    if Model is None:
        raise Exception("Attempted to make chat gpt chat message(s) but model information is not initialized")

    try:
        new_messages = message_length_check(Model.tokenizer, messages, 18000)
        messages = new_messages
        response = Model.client.chat.completions.create(
            model=Model.name,
            messages=[dataclasses.asdict(message) for message in messages],
            temperature=DEFAULT_TEMPERATURE,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            n=1,
            stop=None
        )
    except Exception as e:
        print("GPT Error:", str(e))
        if "context_length_exceeded" in str(e):
            messages = message_length_check(Model.tokenizer, messages, 16200)
            print("AFTER CHANGE MESSAGE LEN:", len(messages))
            print(messages)
            response = Model.client.chat.completions.create(
                model=Model.name,
                messages=[dataclasses.asdict(message) for message in messages],
                max_tokens=MAX_TOKENS,
                temperature=DEFAULT_TEMPERATURE,
                top_p=1,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                n=1,
            )
        else:
            assert False, "GPT API error: " + str(e)

    output= response.choices[MESSAGE_CHOICE_INDEX].message.content

    input_tokens:int = sum([len(Model.tokenizer.tokenize(msg.content)) for msg in messages])
    output_tokens:int = sum([len(Model.tokenizer.tokenize(msg)) for msg in output])

    return ModelChatResult(messages, output, input_tokens, output_tokens)
