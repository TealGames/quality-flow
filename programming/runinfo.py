from model_controller import *
from model_utils import *
from dataset import *

RUN_ALL_DATASET_PROBLEMS_VALUE: int = -1

class RunInfo:
    model_name: ModelName
    dataset_name: DatasetName
    dataset: Dataset
    dataset_problem_limit:int
    iterations:int
    clarifier_attempts: int
    solutions_per_task: int
    
    def __init__(self, model_name:str, dataset_name: str, dataset:Dataset, problem_limit:int, iterations:int, clarifier_attempts:int, solutions_per_task: int):
        maybe_model_name= get_model_name(model_name)
        assert maybe_model_name is not None, f"Attempted to convert invalid model to enum: {model_name}"

        self.model_name= maybe_model_name
        self.dataset_name= get_dataset_name(dataset_name)
        self.dataset= dataset
        self.dataset_problem_limit= problem_limit
        self.iterations= iterations
        self.clarifier_attempts= clarifier_attempts
        self.solutions_per_task= solutions_per_task

    def has_dataset_problem_limit(self)-> bool:
        return self.dataset_problem_limit!= RUN_ALL_DATASET_PROBLEMS_VALUE