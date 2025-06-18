import model
from model_utils import *
from dataset import *

RUN_ALL_DATASET_PROBLEMS_VALUE: int = -1

class RunInfo:
    model_name: ModelName
    dataset_name: DatasetName
    dataset: Dataset
    dataset_problem_limit:int
    iterations:int
    
    def __init__(self, model_name:str, dataset_name: str, dataset:Dataset, problem_limit:int, iterations:int):
        self.model_name=get_model_name(model_name)
        self.dataset_name= get_dataset_name(dataset_name)
        self.dataset= dataset
        self.dataset_problem_limit= problem_limit
        self.iterations= iterations

    def has_dataset_problem_limit(self)-> bool:
        return self.dataset_problem_limit!= RUN_ALL_DATASET_PROBLEMS_VALUE