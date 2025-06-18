from model_utils import *
from enum import Enum
import re

SYMBOL_TAG_START= '['
SYMBOL_TAG_END= ']'

class TagType(Enum):
    PROGRAM= 0
    INPUT= 1,
    OUTPUT= 2
    VISIBLE_TEST= 3
    UNIT_TEST= 4
    PROMPT= 5

CODE_WRITER_SYSTEM_MESSAGE: Message=  Message(
    role="system",
    content="You are a Python writing assistant that only responds with Python programs to solve a Python writing problem.")

PRINT_ADDER_SYSTEM_MESSAGE: Message=  Message(
    role="system",
    content="You are a Python writing assistant that only responds with Python programs with PRINT statements")

def wrap_in_tag(text: str, tag: TagType) -> str:
    return f"{get_start_tag(tag)}\n{text}\n{get_end_tag(tag)}"

def get_start_tag(tag: TagType)-> str:
    return f"{SYMBOL_TAG_START}{str(tag.name) + ' Start'}{SYMBOL_TAG_END}"

def get_end_tag(tag: TagType)-> str:
    return f"{SYMBOL_TAG_START}{str(tag.name) + ' End'}{SYMBOL_TAG_END}"