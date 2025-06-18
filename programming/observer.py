import os
from pathlib import Path
from datetime import datetime
from typing import Dict
from runinfo import *
from dataset import *

LogFile: str = "run_log_@"
LogPath: Path= Path("")

class PromptInfo:
    def __init__(self):
        self.SolutionPlanCount=0
        self.PlanVerificationCount=0
        self.PlanVerificationCheckCount=0
        self.CodeAttemptCount=0

AllPromptInfo: dict[str, PromptInfo]= {}
CurrentPromptKey: str = ""

def observer_init(rootDir: Path, maxIters:int) -> None:
    global LogFile, LogPath
    LogFile= LogFile+ str(datetime.now().strftime("%Y-%m-%d_%H-%M-%S")) + ".txt"
    LogPath= rootDir / LogFile

    LogPath.parent.mkdir(parents=True, exist_ok=True)
    LogPath.touch()

def observer_log_benchmark(run_info:RunInfo) -> None:
    global LogPath
    write_file(LogPath, f"Dataset: {run_info.dataset_name.name}\nModel:{run_info.model_name.name}\n" +
              f"LimitedPrompts:{run_info.dataset_problem_limit}\n" if run_info.has_dataset_problem_limit() else ""+ f"MaxIterations:{run_info.iterations}")

def observer_log_task_result(task: DatasetTask, task_result: DatasetTaskResult, task_success: bool) -> None:
    global LogPath
    write_file(LogPath, f"\n\nTask:{task.get_id()}\nCodeGenerations:{task_result.code_generations}\nDebugIterations:{task_result.debug_iterations}\n"
               f"SynthesizedTestsCount:{task_result.synthesized_test_count}\nFilteredTestCount:{task_result.filtered_test_count}\nPassed:{task_success}")

def observer_finish_tasks(total_passed:int, total_prompts:int):
    global LogPath
    write_file(LogPath, f"\n\nPassedCount:{total_passed}\nTotalPrompts:{total_prompts}\nAccuracy:{total_passed/ total_prompts}%")
               
def write_file(path:Path, lines:str):
    with open(path, "a") as file:
        file.write(lines+"\n")
