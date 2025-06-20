from runinfo import *
from dataset import *
from typing import List, NamedTuple
from message_globals import *
from model_controller import *
import multiprocessing
import sys
from io import StringIO
from threading import Thread
import ast
import astunparse

from test_designer import SynthesizedTest
from code_generator import prepare_function_from_generated_code

class CodeExecutionResult():
    def __init__(self, passed_test_count: int, failed_test_outputs:list[str], failed_timeout_test_indices:List[int], timeout_test_indices:List[int]):
        self.passed_test_count= passed_test_count
        self.failed_test_outputs= failed_test_outputs
        self.failed_timeout_test_indices= failed_timeout_test_indices
        self.timeout_test_indices= timeout_test_indices

    def did_pass_all_tests(self)->bool:
        return len(self.failed_timeout_test_indices)==0
    
    def had_timeout_test(self)->bool:
        return len(self.timeout_test_indices)>0

class PropagatingThread(Thread):
    def run(self):
        self.exc = None
        try:
            if hasattr(self, '_Thread__target'):
                # Thread uses name mangling prior to Python 3.
                self.ret = self._Thread__target(*self._Thread__args, **self._Thread__kwargs)
            else:
                self.ret = self._target(*self._args, **self._kwargs)
        except Exception as e:
            self.exc = e

    def join(self, timeout=None):
        super(PropagatingThread, self).join(timeout)
        if self.exc:
            raise self.exc
        if self.is_alive():
            return None
        return self.ret
    
    def terminate(self):
        self._stop()


def debug_code(run_info:RunInfo, task:DatasetTask, program:str, synthesized_tests:List[SynthesizedTest])-> str:
    test_results_info= ""
    for test in synthesized_tests:
        test_result: CodeExecutionResult = function_with_timeout_process(program, [test.get_as_assert(task.get_created_func_name())])
        #since we check each synthesized test one at a time, first output message is the only one that matters
        test_output_message= "Passed" if test_result.did_pass_all_tests() else test_result.failed_test_outputs[0]
        test_results_info += (f"Test Case Input:{test.input}\nOutput:{test.output}\nTest Result:{test_output_message}\n\n")

    #TODO: what if we added print statements for all variable values at a given point?
    chat_result:ModelChatResult = model_chat(run_info.model_name, [
            CODE_WRITER_SYSTEM_MESSAGE,
            Message(
                role="user",
                content=f"Instructions: you are given a problem within the tags \"{get_start_tag(TagType.PROMPT)}\" and \"{get_end_tag(TagType.PROMPT)}\""
                f"as well as a generated program attempting to solve the problem, which will be given in program tags, \"{get_start_tag(TagType.PROGRAM)}\" and \"{get_end_tag(TagType.PROGRAM)}\", "
                f"and synthesized test cases for this problem with their respective output when run on the program given (in test tags \"{get_start_tag(TagType.UNIT_TEST)}\" and \"{get_end_tag(TagType.UNIT_TEST)}\""
                f"Thinking step by step, use the information given to first analyze why the program fails the test(s) and then revise the program so it would not fail the tests based on your step-by-step analysis."
                f"Place the new revised program enclosed in output tags \"{get_start_tag(TagType.OUTPUT)}\" and \"{get_end_tag(TagType.OUTPUT)}\"."
                f"{wrap_in_tag(task.get_prompt(), TagType.PROMPT)}\n\n{wrap_in_tag(program, TagType.PROGRAM)}\n\n{wrap_in_tag(test_results_info, TagType.UNIT_TEST)}")
        ])
    
    return prepare_function_from_generated_code(run_info.dataset_name, task.get_prompt(), program, task.get_created_func_name())

def function_with_timeout_process(code_str: str, asserts: List[str], timeout= 60) ->CodeExecutionResult:
    result=find_syntax_error(code_str)
    # syntax_error
    if result!=None:
        return CodeExecutionResult(0, [f"{asserts[0]} # Real Execution Output: {result}"], [], [])
    with multiprocessing.Pool(processes = multiprocessing.cpu_count() - 2) as pool:
        tasks = [(code_str, ast, timeout) for ast in asserts]
        pool_results = pool.starmap(exec_ast_fn, tasks)
        
        passed_tests = sum(map(lambda x: 1 if x[0] == 0 else 0, pool_results))
        
        # failed_tests_list: the indexes of the assertions that are failed or timeout
        failed_tests_list = [i for i, x in enumerate(pool_results) if x[0] < 0]
        timeout_list = [i for i, x in enumerate(pool_results) if x[0] == -1]

    with multiprocessing.Pool(processes=multiprocessing.cpu_count() - 2) as pool:
        failed_and_timeout_tests = [x[1] for x in pool_results if x[0] < 0]
        tasks = [(code_str, ast, timeout) for ast in failed_and_timeout_tests]
        pool_results = pool.starmap(eval_ast_fn, tasks)
        
        failed_printed_output_list = [x[1] for x in pool_results]
        failed_tests = ["{} # Real Execution Output: {}".format(x[2], x[0]) for x in pool_results]

    return CodeExecutionResult(passed_tests, failed_tests, failed_tests_list, timeout_list)

def find_syntax_error(code):
    try:
        exec(code)
        return None
    except SyntaxError as e:
        error_message=""
        try:
            error_message = f'  File "{e.filename}", line {e.lineno}\n'
        except:
            pass
        try:
            error_message += f'    {e.text.strip()}\n'
        except:
            pass
        try:
            error_message += ' ' * (e.offset + 3) + '^\n'
        except:
            pass
        try:
            error_message += f"{e.__class__.__name__}: {e.msg}\n"
        except:
            pass
        return error_message
    except Exception as e:
        return None
    
def function_with_timeout(func, args, timeout):
    result_container = []

    def wrapper():
        result_container.append(func(*args))

    try:
        thread = PropagatingThread(target=wrapper)
        thread.start()
        thread.join(timeout)

        if thread.is_alive(): # timeout
            return -1, None
        else: # correctly run
            return 0, result_container[0] # list of sometime
    except Exception as e:
        return -2, e # incorrectly run
    
def exec_ast_fn(code, ast, timeout):
    # run code + completed one ast
    # consider timeout
    # extract stdout

    imports = 'from typing import *'
    code = f'{imports}\n{code}\n{ast}'

    try:
        rtn = function_with_timeout(exec, (code, globals()), timeout)
    except Exception as e:
        rtn = (-2, e)
    finally:
        if rtn[0] == -1:
            return rtn[0], ast
        elif rtn[0] == -2: # incorrect result
            return rtn[0], ast
        else:
            return 0, ast
        
def eval_ast_fn(code, ast, timeout):
    original_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        exec(f"from typing import *\n{code}", globals())
        ast_func_call = get_call_str(ast)
        rtn = function_with_timeout(eval, (ast_func_call, globals()), timeout)

    except Exception as e:
        rtn = (-2, e)
    finally:
        sys.stdout.flush()
        captured_output = sys.stdout.getvalue()
        sys.stdout = original_stdout

        if rtn[0] == -1:
            return "TIMEOUT", captured_output + "\n TIMEOUT", ast
        elif rtn[0] == -2:  # such as OOIndex
            return str(rtn[1]), captured_output + "\n " + str(rtn[1]), ast
        else:  # can run, but wrong results
            return str(rtn[1]), captured_output, ast
        
def get_call_str(assert_statement: str) -> str:
    ast_parsed = ast.parse(assert_statement)
    try:
        call_str = ast_parsed.body[0].test.left # type: ignore
    except:
        call_str = ast_parsed.body[0].test # type: ignore

    return astunparse.unparse(call_str).strip()
    
