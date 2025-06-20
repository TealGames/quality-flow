from runinfo import *
from dataset import *
from typing import List
from message_globals import *
from model_controller import *

def clarify_problem(run_info:RunInfo, task:DatasetTask, debugged_code:str)-> str:
    test_asserts_str= ""
    for test_assert in task.get_test_asserts():
        test_asserts_str+=f"{test_assert}\n"
    chat_result:ModelChatResult = model_chat(run_info.model_name, [
                CODE_WRITER_SYSTEM_MESSAGE,
                Message(
                    role="user",
                    content=f"Instructions: given a coding problem, visible tests and code that has been debugged in an attempt to solve the problem but has failed code quality checks, "
                    "explain the initial coding problem prompt in detail in an effort to better clarify and misunderstandings. "
                    f"The prompt will be contained in \"{get_start_tag(TagType.PROMPT)}\" and \"{get_end_tag(TagType.PROMPT)}\","
                    f"the visible tests within the test tags \"{get_start_tag(TagType.VISIBLE_TEST)}\" and \"{get_end_tag(TagType.VISIBLE_TEST)}\", "
                    f"and the debugged code in \"{get_start_tag(TagType.PROGRAM)}\" and \"{get_end_tag(TagType.PROGRAM)}\"."
                    f"{wrap_in_tag(task.get_prompt(), TagType.PROMPT)}\n\n{wrap_in_tag(test_asserts_str, TagType.VISIBLE_TEST)}\n\n{wrap_in_tag(debugged_code, TagType.PROGRAM)}"
                    )
            ])
    return chat_result.output