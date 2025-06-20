from runinfo import *
from dataset import *
from typing import List
from message_globals import *
from model_controller import *
from utils import regex_escape_special

TEMPERATURE:float =0.1
TEST_GENERATION_ROUNDS: int = 5
TESTS_GENERATED_PER_ROUND: int = 10

class SynthesizedTest:
    def __init__(self, input: str, output: str):
        self.input= input
        self.output= output

    def get_as_assert(self, function_name:str)-> str:
        return f"assert {function_name}({self.input}) == {self.output}"


def design_tests(run_info:RunInfo, task : DatasetTask) -> List[SynthesizedTest]:
    for i in range(TEST_GENERATION_ROUNDS):
        chat_result:ModelChatResult = model_chat(run_info.model_name, [
                    CODE_WRITER_SYSTEM_MESSAGE,
                    Message(
                        role="user",
                        content=f"Instructions: given a program contained within program tags: \"{get_start_tag(TagType.PROGRAM)}\" and \"{get_end_tag(TagType.PROGRAM)}\""
                        f"as well as visible tests within the test tags \"{get_start_tag(TagType.VISIBLE_TEST)}\" and \"{get_end_tag(TagType.VISIBLE_TEST)}\", "
                        f"generate {TESTS_GENERATED_PER_ROUND} common case unit tests such that each test is enclosed with test tags \"{get_start_tag(TagType.UNIT_TEST)}\" and \"{get_end_tag(TagType.UNIT_TEST)}\""
                        f"and that each unit test contains the input as it would be provided to the function with each input value separated by a space enclosed in tags \"{get_start_tag(TagType.INPUT)}\" and \"{get_end_tag(TagType.INPUT)}\"."
                        f"Each unit test should also include the expected output from the unit test enclosed in output tags: \"{get_start_tag(TagType.OUTPUT)}\" and \"{get_end_tag(TagType.OUTPUT)}\""
                        f"Here is an example of the formatting: "
                        )
                ], TEMPERATURE)
    
    return extract_unit_tests(chat_result.output)
    
def extract_unit_tests(message: str) -> List[SynthesizedTest]:
    pattern = fr"{regex_escape_special(get_start_tag(TagType.UNIT_TEST))}(.*?){regex_escape_special(get_end_tag(TagType.UNIT_TEST))}"
    blocks = re.findall(pattern, message, re.DOTALL)

    results: List[SynthesizedTest] = []
    for block in blocks:
        input_match = re.search(fr"{regex_escape_special(get_start_tag(TagType.INPUT))}(.*?){regex_escape_special(get_start_tag(TagType.INPUT))}", block, re.DOTALL)
        output_match = re.search(fr"{regex_escape_special(get_start_tag(TagType.OUTPUT))}(.*?){regex_escape_special(get_start_tag(TagType.OUTPUT))}", block, re.DOTALL)
        if input_match and output_match:
            input_str = input_match.group(1).strip()
            output_str = output_match.group(1).strip()
            #TODO: right now the full string, even if there are multiple args for input/output is treated as one
            results.append(SynthesizedTest(input_str, output_str))
    return results
