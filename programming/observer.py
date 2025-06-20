import os
from pathlib import Path
from datetime import datetime
from typing import Dict
from runinfo import *
from dataset import *

log_file: str = "run_log_@"
log_path: Path= Path("")

def observer_init(output_dir: Path, max_iterations:int) -> None:
    global log_file, log_path
    log_file= log_file+ str(datetime.now().strftime("%Y-%m-%d_%H-%M-%S")) + ".txt"
    log_path= output_dir / log_file

    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.touch()

def observer_log_benchmark(run_info:RunInfo) -> None:
    global log_path
    write_file(log_path, f"Dataset: {run_info.dataset_name.name}\nModel:{run_info.model_name.value}\n" +
              f"LimitedPrompts:{run_info.dataset_problem_limit}\n" if run_info.has_dataset_problem_limit() else ""+ 
              f"MaxIterations:{run_info.iterations}\nMaxClarifyAttempts:{run_info.clarifier_attempts}SolutionsPerTask:{run_info.solutions_per_task}")

def observer_log_task_result(task: DatasetTask, task_result: DatasetTaskResult, passed_at_solution_index: int) -> None:
    global log_path
    write_file(log_path, f"\n\nTask:{task.get_id()}\nCodeGenerations:{task_result.code_generations}\nDebugIterations:{task_result.debug_iterations}\n"
               f"ClarifierAttempts:{task_result.clarify_iterations}\nSynthesizedTestsCount:{task_result.synthesized_test_count}\n"
               f"FilteredTestCount:{task_result.filtered_test_count}\nPassed:{passed_at_solution_index!=-1}\n"
               f"SolutionNumber(0-indexed): {'NONE' if passed_at_solution_index==-1 else passed_at_solution_index}")

def observer_finish_tasks(total_passed:int, total_prompts:int):
    global log_path
    write_file(log_path, f"\n\nPassedCount:{total_passed}\nTotalPrompts:{total_prompts}\nAccuracy:{total_passed/ total_prompts*100}%")
               
def write_file(path:Path, lines:str):
    with open(path, "a") as file:
        file.write(lines+"\n")
