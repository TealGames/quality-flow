
from model_controller import *
from message_globals import *
from typing import Tuple, List, Dict
from runinfo import *
import re
from dataset import *

IMPORT_HEADER:str = "from typing import *\nimport math\nfrom heapq import *\nimport itertools\nimport re\nimport typing\nimport heapq\n_str=str\nimport re\nimport hashlib\nimport heapq\nimport collections\nfrom collections import *\nfrom itertools import combinations\nfrom math import prod\nfrom itertools import combinations_with_replacement\nfrom  decimal import Decimal, getcontext\nimport numpy as np\n"
TEMPERATURE:float= 0

def generate_code(run_info:RunInfo, task: DatasetTask, diversified_prompt: str, visible_assert_tests:str, problem_func_name:str)-> str:
    chat_result:ModelChatResult = model_chat(run_info.model_name, [
            CODE_WRITER_SYSTEM_MESSAGE,
            Message(
                role="user",
                content=f"Instructions: You will be given a coding problem prompt contained within \"{get_start_tag(TagType.PROMPT)}\" and \"{get_end_tag(TagType.PROMPT)}\""
                        f"and the tests that the code must pass will be contained within \"{get_start_tag(TagType.VISIBLE_TEST)}\" and \"{get_end_tag(TagType.VISIBLE_TEST)}\"."
                        f"{diversified_prompt}"
                        f"When you see \"Let\'s generate the program\" begin generating the program."
                        f"\n\n{wrap_in_tag(task.get_prompt(), TagType.PROMPT)}\n\n{wrap_in_tag(visible_assert_tests, TagType.VISIBLE_TEST)}\n\n \"Let\'s generate the program\"",
                ),
        ], TEMPERATURE)
    
    generated_program: str= chat_result.output
    return prepare_function_from_generated_code(run_info.dataset_name, task.get_prompt(), generated_program, problem_func_name)

def get_code_gen_prompt_from_iteration(task: DatasetTask, iteration_index:int)-> str:
    if (iteration_index==0):
        return ("Your goal is to generate the program that follows the given prompt and passes the visible tests given")
    else:
        raise ValueError(f"Attempted to get prompt for self debug iteration:{iteration_index} for prompt:{task.get_id()} but none were found")
    
def prepare_function_from_generated_code(dataset_name:DatasetName, prompt:str, generated_program:str, entry_point:str, add_header = True) ->str:
    if dataset_name in [DatasetName.MBPP, DatasetName.HumanEval, DatasetName.APPS, DatasetName.CodeContests, DatasetName.LiveCode]:
        function_impl: str=""
        if (prompt in generated_program) or (('def ' + entry_point + '(') in generated_program):
            function_impl = generated_program
        else:
            function_impl = prompt + "\n" + generated_program
        # Add auxilary function
        function_impl=filter_function(function_impl)
        funcs = get_function(prompt)
        seed_funcs = [func[0] for func in get_function(generated_program)]
        for func in funcs:
            if func[0] not in seed_funcs:
                function_impl = func[1] + "\n" + function_impl
        # Add comments
        if not find_comment(function_impl, entry_point):
            function_impl = fix_func_impl_comments(function_impl, prompt, entry_point)
    # Add import header
    if add_header and IMPORT_HEADER not in function_impl:
        function_impl = IMPORT_HEADER + function_impl

    return function_impl

def get_function(prompt)-> List[List[str]]:
    lines = prompt.split('\n')
    current_function = ""
    functions: List[List[str]] = []
    for i, l in enumerate(lines):
        if l.startswith("def "):
            if current_function == "":
                current_function = l
            else:
                functions.append([function_name, current_function])
                current_function = l
            function_name = l.split("def ")[1].split("(")[0]
        elif current_function != "":
            current_function += "\n" + l
    return functions

def filter_function(func_imp):
    problem_description= extract_docstring(func_imp)
    import_statements= capture_import_statements(func_imp)
    func_imp=func_imp.replace("```","")
    func_imp=func_imp[func_imp.find("def"):]
    func_lines=[]
    test_case_pattern = re.compile(r'test case', re.IGNORECASE)
    assert_pattern = re.compile(r'assert', re.IGNORECASE)
    start_program_pattern=re.compile(r'Start Program', re.IGNORECASE)
    end_program_pattern=re.compile(r'End Program', re.IGNORECASE)
    start_fixed_program_pattern=re.compile(r'Start Fixed Program', re.IGNORECASE)
    end_fixed_program_pattern=re.compile(r'End Fixed Program', re.IGNORECASE)
    start_fix_explanation=re.compile(r'Fixing Explanation',re.IGNORECASE)
    start_explanation_adjustments = re.compile(r'Explanation Adjustments', re.IGNORECASE)


    for line in func_imp.split("\n"):
        if re.search(start_program_pattern,line) or re.search(end_program_pattern,line) or re.search(start_fixed_program_pattern,line) or re.search(end_fixed_program_pattern,line):
            continue
        if line not in problem_description and (contains_test_case(line) or contains_assert(line) or contains_fix(line) or contains_adjust(line)):
            break
        func_lines.append(line)
    func_lines=import_statements+func_lines
    func_imp="\n".join(func_lines)
    return func_imp

def contains_test_case(line: str) -> bool:
    # Define the regular expression pattern to search for "test case"
    test_case_pattern = re.compile(r'test case', re.IGNORECASE)

    # Check if the line is a print statement
    if line.strip().startswith('print('):
        return False

    # Search for the pattern in the line
    return bool(re.search(test_case_pattern, line))

def extract_docstring(function_str: str) -> str:
    # Regular expression to find the content between triple quotes
    docstring_pattern = re.compile(r'""".*?"""', re.DOTALL)

    # Search for the pattern in the function string
    match = docstring_pattern.search(function_str)

    if match:
        # Extract and clean up the docstring
        docstring = match.group(0)
        docstring = docstring.strip('"""')
        return docstring.strip()
    else:
        return ""
    
def capture_import_statements(code: str) -> list:
    """
    Capture all import statements from the given Python code.

    Args:
    code (str): The string containing the Python code.

    Returns:
    list: A list of import statements found in the code.
    """
    matches = re.findall(r'^\s*(import\s+\w+(\s*,\s*\w+)*|from\s+\w+(\.\w+)*\s+import\s+\w+(\s*,\s*\w+)*)', code,
                         re.MULTILINE)
    return [match[0] for match in matches]

def contains_assert(line: str) -> bool:
    # Define the regular expression pattern to search for "test case"
    assert_pattern = re.compile(r'assert', re.IGNORECASE)

    # Check if the line is a print statement
    if line.strip().startswith('print('):
        return False

    # Search for the pattern in the line
    return bool(re.search(assert_pattern, line))

def contains_fix(line: str) -> bool:
    # Define the regular expression pattern to search for "test case"
    start_fix_explanation=re.compile(r'Fixing Explanation',re.IGNORECASE)

    # Check if the line is a print statement
    if line.strip().startswith('print('):
        return False

    # Search for the pattern in the line
    return bool(re.search(start_fix_explanation, line))

def contains_adjust(line: str) -> bool:
    # Define the regular expression pattern to search for "test case"
    start_explanation_adjustments = re.compile(r'Explanation Adjustments', re.IGNORECASE)

    # Check if the line is a print statement
    if line.strip().startswith('print('):
        return False

    # Search for the pattern in the line
    return bool(re.search(start_explanation_adjustments, line))

def find_comment(func_impl: str, entry: str ) -> bool:
    func_impl_lines = func_impl.split('\n')
    for i, line in enumerate(func_impl_lines):
        if line.startswith('def ' + entry + "("):
            break
    func_body = "\n".join(func_impl_lines[i:])
    if func_body.find('\"\"\"') != -1 or func_body.find('\'\'\'') != -1:
        return True
    return False

def fix_func_impl_comments(func_impl: str, prompt: str, entry) -> str:
    # extract comments from prompt and insert them into func_impl after the function header
    if prompt.find('\"\"\"') != -1:
        comments = prompt.split('\"\"\"')[1]
    elif prompt.find('\'\'\'') != -1:
        comments = prompt.split('\'\'\'')[1]
    # Get the function header
    func_impl_lines = func_impl.split('\n')
    for i, line in enumerate(func_impl_lines):
        if line.startswith('def') and entry in line:
            break
    # Insert comments after the function header
    func_impl_lines.insert(i+1, '    \"\"\"' + comments + '\"\"\"')
    return '\n'.join(func_impl_lines)
    
    
    
