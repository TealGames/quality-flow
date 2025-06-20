from runinfo import *
from typing import Tuple, List, Dict
from model_controller import *
from message_globals import *
from dataset import *
import re
from utils import regex_escape_special

def check_code_quality(run_info:RunInfo, task:DatasetTask, program:str)-> bool:
    #TODO: should each test be a separate message?
    for test in task.split_asserts_by_io:
        chat_result:ModelChatResult = model_chat(run_info.model_name, [
                OUTPUT_REASONER_SYSTEM_MESSAGE,
                Message(
                    role="user",
                    content=f"Instructions: thinking step by step, determine the output of the program contained within the \"{get_start_tag(TagType.PROGRAM)}\" and \"{get_end_tag(TagType.PROGRAM)}\" tags"
                    f"given the input specified in the input tags \"{get_start_tag(TagType.INPUT)}\" and \"{get_end_tag(TagType.INPUT)}\"."
                    f"Your response should be contained within \"{get_start_tag(TagType.OUTPUT)}\" and \"{get_end_tag(TagType.OUTPUT)}\" "
                    f"{wrap_in_tag(program, TagType.PROGRAM)}\n\n{wrap_in_tag(test[0], TagType.INPUT)}"
                    ),
            ])
        if (extract_output(chat_result.output)!=test[1]):
            return False
        
    return True

def extract_output(chat_message: str)-> str:
    match = re.search(rf"{regex_escape_special(get_start_tag(TagType.OUTPUT))}"
                      rf"(.*?){regex_escape_special(get_start_tag(TagType.OUTPUT))}", chat_message)
    if match:
        return match.group(1)
    else:
        return ""
    
def extract_asserts(test: str)-> List[List[str]]:
    pattern = r"assert\s+candidate\((.*?)\)\s*==\s*(.+)"
    matches = re.findall(pattern, test)
    result = []
    for args, expected in matches:
        # Remove trailing comments or newlines from expected
        expected = expected.split('#')[0].strip()
        result.append([args.strip(), expected])
    return result
