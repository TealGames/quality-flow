from runinfo import *
from dataset import *
from typing import List
from message_globals import *
from model_controller import *
from test_designer import SynthesizedTest
from utils import regex_escape_special

def filter_valid_tests(run_info:RunInfo, task:DatasetTask, synthesizedTests: List[SynthesizedTest]) -> List[SynthesizedTest]:
    valid_tests: List[SynthesizedTest]= []
    for test in synthesizedTests:
        chat_result:ModelChatResult = model_chat(run_info.model_name, [
                    OUTPUT_REASONER_SYSTEM_MESSAGE,
                    Message(
                        role="user",
                        content=f"Instructions: given a prompt contained within prompt tags: \"{get_start_tag(TagType.PROMPT)}\" and \"{get_end_tag(TagType.PROMPT)}\""
                        f"as well as visible tests within the test tags \"{get_start_tag(TagType.VISIBLE_TEST)}\" and \"{get_end_tag(TagType.VISIBLE_TEST)}\", "
                        f"thinking step by step and using the knowledge of the problem given, determine what the output would be for the input which will be given in input tags: \"{get_start_tag(TagType.INPUT)}\" and \"{get_end_tag(TagType.INPUT)}\"."
                        f"Write the output enclosed in output tags: \"{get_start_tag(TagType.OUTPUT)}\" and \"{get_end_tag(TagType.OUTPUT)}\"."
                        f"{wrap_in_tag(task.get_prompt(), TagType.PROMPT)}\n\n{wrap_in_tag(test.input, TagType.VISIBLE_TEST)}")
                ])
        #TODO: can we say step by step and only allow the output result as message oor would that ruin it?
        reasoned_output= extract_output(chat_result.output)
        if test.output== reasoned_output:
            valid_tests.append(test)

    return valid_tests

def extract_output(message: str) -> str:
    match = re.search(fr"{regex_escape_special(get_start_tag(TagType.OUTPUT))}"
                      fr"(.*?){regex_escape_special(get_start_tag(TagType.OUTPUT))}", message, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    else:
        return ""