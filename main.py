import os
import argparse
from pathlib import Path
from datetime import datetime
from observer import *
from model import *
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
DEFAULT_OUTPUT_DIR: str= "output"

USE_TEXT_QUALITY_CHECKER: bool = True

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, help="The name of the model to run")
    parser.add_argument("--output_dir", type=str,
                        help="The root logging directory", default= DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dataset_name", type=str,
                        help="The name of the benchmark. Used to retrieve problems from default datasets")
    parser.add_argument("--dataset_path", type=str,
                        help="The path of the benchmark dataset. Used only for custom benchmarks not included in repository", default= "")
    parser.add_argument("--problem_count", type=str,
                        help="The number of problems to run from the dataset", default= RUN_ALL_DATASET_PROBLEMS_VALUE)               
    parser.add_argument("--max_iters", type=int,
                        help="The maximum number of self-improvement iterations", default=10)
    args = parser.parse_args()
    return args

def create_benchmark_path(benchmark:str)->str:
    global BENCHMARK_PATH_ROOT
    return f"{BENCHMARK_PATH_ROOT}/{benchmark}/{BENCHMARK_FILE}"

def solve_coding_task(run_info: RunInfo, task: DatasetTask)->DatasetTaskResult:
    generated_code = generate_code(run_info, task.get_prompt(), task.get_test_asserts_consolidated(), task.get_created_func_name())
    passes_quality_checker= check_code_quality(run_info, task, generated_code)
    if (passes_quality_checker):
        return DatasetTaskResult(generated_code, 1, 0, 0, 0)
    
    synthesized_tests= design_tests(run_info, task)
    filteredTests: List[SynthesizedTest] = []
    if (USE_TEXT_QUALITY_CHECKER):
        filteredTests= filter_valid_tests(run_info, task, synthesized_tests)
    else:
        filteredTests= synthesized_tests

    debugged_code= ""
    for i in range(run_info.iterations):
        debugged_code= debug_code(run_info, task, generated_code, filteredTests)
        passes_quality_checker= check_code_quality(run_info, task, debugged_code)
        if (passes_quality_checker):
            #Note: adding 2 because 1 for first generation and 1 for iteration offset due to 0 index
            return DatasetTaskResult(debugged_code, i+2, i+1, len(synthesized_tests), len(filteredTests))
    
    clarified_problem= task.get_prompt()
    clarified_problem+= f"\nClarification:{clarify_problem(run_info, task, debugged_code)}" 
    clarified_code= generate_code(run_info, clarified_problem, task.get_test_asserts_consolidated(), task.get_created_func_name())
    passes_quality_checker= check_code_quality(run_info, task, clarified_code)

    return DatasetTaskResult(clarified_code if passes_quality_checker else generated_code, 
                             run_info.iterations+2, run_info.iterations, len(synthesized_tests), len(filteredTests))
    
def main(args):
    global BENCHMARK_PATH_ROOT

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    if (args.dataset_name!="" and args.dataset_path!=""):
        raise Exception(f"Attempted to find dataset but run started with both a dataset name:'{args.dataset_name}'"
                        f"and path:'{args.dataset_path}' which is not allowed")
    
    dataset_path: str= args.dataset_path if args.dataset_path!="" else create_benchmark_path (args.benchmark)
    dataset= Dataset(dataset_path)
    run_info= RunInfo(args.model, args.dataset_name, dataset, args.problem_count, args.max_iters)
    model_init(run_info.model_name)

    observer_init(Path(args.root_dir), args.max_iters)
    observer_log_benchmark(run_info)
    
    pass_count: int =0
    for task in dataset.tasks:
        code_task_result= solve_coding_task(run_info, task)

        code_test_result= function_with_timeout_process(code_task_result.code, task.get_test_asserts())
        passed_tests= code_test_result.did_pass_all_tests()
        if (passed_tests):
            pass_count+=1

        observer_log_task_result(task, code_task_result, passed_tests)

    observer_finish_tasks(pass_count, len(dataset.tasks))

if __name__ == "__main__":
    args = get_args()
    main(args)
