import os
import argparse
from pathlib import Path
from datetime import datetime
from observer import *
from model_controller import *
from utils import *
from dataset import *

from code_generator import *
from code_quality_checker import *
from test_designer import *
from test_quality_checker import *
from self_debugger import *
from problem_clarifier import *

BENCHMARK_PATH_ROOT: Path= Path("../benchmarks_with_tests")
BENCHMARK_FILE= "probs.jsonl"
DEFAULT_OUTPUT_DIR: str= "../output"
USE_TEXT_QUALITY_CHECKER: bool = True

# ---------------------------------------------------------
#           PARAMETERS (DEFAULTS AS FOUND IN PAPER)
#----------------------------------------------------------
DEFAULT_MAX_DEBUG_ITERATIONS: int= 3
DEFAULT_CLARIFIER_ATTEMPTS: int = 3
DEFAULT_TASK_SOLUTION_COUNT:int = 6

def get_args():
    global DEFAULT_OUTPUT_DIR, RUN_ALL_DATASET_PROBLEMS_VALUE, DEFAULT_MAX_DEBUG_ITERATIONS

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, help="The name of the model to run")
    parser.add_argument("--output_dir", type=str,
                        help="The root logging directory", default= DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dataset_name", type=str,
                        help="The name of the benchmark. Used to retrieve problems from default datasets")
    parser.add_argument("--dataset_path", type=str,
                        help="The path of the benchmark dataset. Used only for custom benchmarks not included in repository", default= "")
    parser.add_argument("--problem_count", type=int,
                        help="The number of problems to run from the dataset", default= RUN_ALL_DATASET_PROBLEMS_VALUE)               
    parser.add_argument("--max_iters", type=int,
                        help="The maximum number of self-improvement debug iterations", default=DEFAULT_MAX_DEBUG_ITERATIONS)
    args = parser.parse_args()
    return args

def create_benchmark_path(benchmark:str)->str:
    global BENCHMARK_PATH_ROOT, BENCHMARK_FILE
    return f"{BENCHMARK_PATH_ROOT}/{benchmark}/{BENCHMARK_FILE}"

def solve_coding_task(run_info: RunInfo, task: DatasetTask, solution_index: int)->DatasetTaskResult:
    global USE_TEXT_QUALITY_CHECKER

    #TODO: the research paper says each iteration has diversified prompts, is that model chat prompts or dataset prompts? model chat prompts are diversified in this implementation
    #TODO: paper also mentions zero-shot prompts?
    generated_code = generate_code(run_info, task, get_code_gen_prompt_from_iteration(task, solution_index), 
                                   task.get_test_asserts_consolidated(), task.get_created_func_name())
    code_generation_count: int= 1
    passes_quality_checker= check_code_quality(run_info, task, generated_code)
    if (passes_quality_checker):
        return DatasetTaskResult(generated_code, code_generation_count, 0, 0, 0, 0)
    
    synthesized_tests= design_tests(run_info, task)
    filteredTests: List[SynthesizedTest] = []
    if (USE_TEXT_QUALITY_CHECKER):
        filteredTests= filter_valid_tests(run_info, task, synthesized_tests)
    else:
        filteredTests= synthesized_tests

    debugged_code= ""
    for i in range(run_info.iterations):
        #TODO: diversified prompts here is the chat model prompt for debugging too
        debugged_code= debug_code(run_info, task, get_debug_prompt_from_iteration(task, i), generated_code, filteredTests)
        code_generation_count+=1
        passes_quality_checker= check_code_quality(run_info, task, debugged_code)
        if (passes_quality_checker):
            return DatasetTaskResult(debugged_code, code_generation_count, i+1, 0, len(synthesized_tests), len(filteredTests))
    
    clarified_code= ""
    clarified_problem= ""
    for i in range(DEFAULT_CLARIFIER_ATTEMPTS):
        #TODO: once again diversified prompts is the code gen prompt + clarified info (not dataset prompt) when clarifying
        clarified_problem= get_code_gen_prompt_from_iteration(task, solution_index)
        clarified_problem= f"\nClarification:{clarify_problem(run_info, task, debugged_code)}" 
        clarified_code= generate_code(run_info, task, clarified_problem, task.get_test_asserts_consolidated(), task.get_created_func_name())
        code_generation_count+=1
        passes_quality_checker= check_code_quality(run_info, task, clarified_code)

        if (passes_quality_checker):
            return DatasetTaskResult(clarified_code, code_generation_count, run_info.iterations, i+1, len(synthesized_tests), len(filteredTests))

    return DatasetTaskResult(generated_code, code_generation_count, run_info.iterations, run_info.clarifier_attempts,
                             len(synthesized_tests), len(filteredTests))
    
def main(args):
    global BENCHMARK_PATH_ROOT

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    if (args.dataset_name!="" and args.dataset_path!=""):
        raise Exception(f"Attempted to find dataset but run started with both a dataset name:'{args.dataset_name}'"
                        f"and path:'{args.dataset_path}' which is not allowed")
    
    dataset_path: str= args.dataset_path if args.dataset_path!="" else create_benchmark_path (args.dataset_name)
    dataset= Dataset(dataset_path, args.problem_count)
    run_info= RunInfo(args.model, args.dataset_name, dataset, args.problem_count, args.max_iters, DEFAULT_CLARIFIER_ATTEMPTS, DEFAULT_TASK_SOLUTION_COUNT)
    model_init(run_info.model_name)

    observer_init(Path(args.output_dir), args.max_iters)
    observer_log_benchmark(run_info)
    
    pass_count: int =0
    print(f"Total tasks:{len(dataset.tasks)}")

    for task in dataset.tasks:
        passed_solution_index: int =-1
        for i in range(run_info.solutions_per_task):
            print(f"Starting task:{task.get_id()} Solution #{i}")
            code_task_result= solve_coding_task(run_info, task, i)

            code_test_result= function_with_timeout_process(code_task_result.code, task.get_test_asserts())
            print(f"Completed task :{task.get_id()} Solution #{i}")

            if (code_test_result.did_pass_all_tests()):
                passed_solution_index= i
                pass_count+=1
                break

        observer_log_task_result(task, code_task_result, passed_solution_index)
            
    observer_finish_tasks(pass_count, len(dataset.tasks))
    print(f"Completed all tasks. Check path '{args.output_dir}' for log info")

if __name__ == "__main__":
    args = get_args()
    main(args)
