# quality-flow
Unofficial implementation of the code used in the research paper: https://arxiv.org/pdf/2501.17167

## Installation/Setup

1) Create Conda environment
```
conda create -n qfl python=3.10
conda activate qfl
```
2) Navigate to repository
3) Install required packages
```
python -m pip install -r requirements.txt
```
4) Navigate to 'programming' folder
```
cd ./programming
```

## Running
```
python main.py --model [MODEL_NAME] --output_dir [OUTPUT_DIRECTORY] --dataset_name [DATASET_NAME] --dataset_path [DATASET_PATH] --problem_count [PROBLEM_COUNT] --max_iters [MAX_ITERATIONS]
```
Example run: 
```
python main.py --model gpt-4 --output_dir ../output --dataset_name HumanEval
```

| Argument           | Meaning                                                                                                              |
| ------------------ | -------------------------------------------------------------------------------------------------------------------- |
| MODEL_NAME         | model to run                                                                                                         |
| OUTPUT_DIRECTORY   | dataset task logs/stats                                                                                              |
| DATASET_NAME       | name of dataset to run                                                                                               |
| DATASET_PATH       | path of dataset (OPTIONAL if DATASET_NAME in repository + valid)                                                     |
| PROBLEM_COUNT      | number of problems from dataset to run (OPTIONAL, Default: all)                                                      |
| MAX_ITERATIONS     | max number of debug iterations (OPTIONAL, Default: 10)                                                               |

Available options:
| Argument           | Values                                                                                                               |
| ------------------ | -------------------------------------------------------------------------------------------------------------------- |
| MODEL_NAME         | `gpt-3.5-turbo-0613`,`gpt-3.5-turbo-0125`, `gpt-4`(gpt-4-1106-preview), `gpt-4o`(gpt-4o-2024-05-13),`gpt-4o-mini'    |
| DATASET_NAME       | `HumanEval`, `MBPP`, `HumanEval-ET`,`MBPP-ET`                                                                        |