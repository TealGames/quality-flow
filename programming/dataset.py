from typing import List, Dict, Any, Tuple
from enum import Enum
from pathlib import Path
from utils import read_jsonl

class DatasetName(Enum):
    HumanEval= 0
    MBPP= 1
    APPS= 2
    CodeContests= 3 
    LiveCode= 4

def get_dataset_name(name: str) -> DatasetName:
    return DatasetName[name]

def is_given_dataset(dataset_name: DatasetName):
    return dataset_name in [DatasetName.HumanEval, DatasetName.MBPP]

class DatasetTask:
    def __init__(self, task: Dict[str, Any]):
        self.task= task
        self.split_asserts_by_io: List[Tuple[str, str]] =[]

        for test in self.get_test_asserts():
            try:
                func_args_start_index= test.find('(')
                comparison_index= test.find('==')

                input_end_index= comparison_index-1
                #input end index should end on function closing )
                while (test[input_end_index]==' '):
                    input_end_index-=1

                #move 1 to pass == and then 1 to move to next space
                output_start_index= comparison_index+2
                while(test[output_start_index]== ' '):
                    output_start_index+=1

                self.split_asserts_by_io.append((test[func_args_start_index+1:input_end_index], test[output_start_index]))

            except Exception as e:
                raise Exception(f"Attempted to get test asserts split by input output for dataset task:{self.get_id()} but ran into error:{e}")

    def get_id(self)-> str:
        return self.task['task_id']

    def get_prompt(self)-> str:
        return self.task['prompt']
    
    def get_created_func_name(self)-> str:
        return self.task['entry_point']
    
    def get_test_function(self)-> str:
        return self.task['test']
    
    def get_test_asserts(self)-> List[str]:
        return self.task['given_tests']
    
    def get_test_asserts_consolidated(self)-> str:
        consolidated= ""
        for test in self.get_test_asserts():
            consolidated+=f"{test}\n"
        return consolidated
    
    def get_solution(self)-> str:
        return self.task['canonical_solution']

class Dataset:
    def __init__(self, path: str, problem_limit: int | None= None):
        if path.endswith(".jsonl"):
            dataset = read_jsonl(path, problem_limit)
        else:
            raise ValueError(
                f"Dataset path `{path}` is not supported")
        
        self.tasks: List[DatasetTask]= []
        for task in dataset:
            self.tasks.append(DatasetTask(task))

class DatasetTaskResult:
    code: str
    #the total number of code generations, including debug iterations
    code_generations: int
    debug_iterations: int
    clarify_iterations: int
    synthesized_test_count: int
    #the number of tests that remain after filtering synthesized tests
    filtered_test_count:int

    def __init__(self, code: str, code_generations:int, debug_iterations:int, clarify_iterations:int, synthesized_test_count:int, filtered_test_count:int):
        self.code= code
        self.code_generations= code_generations
        self.debug_iterations= debug_iterations
        self.clarify_iterations= clarify_iterations
        self.synthesized_test_count= synthesized_test_count
        self.filtered_test_count= filtered_test_count

