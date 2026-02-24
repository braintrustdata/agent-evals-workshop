import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from braintrust import Eval, init_dataset, init_function

from agents.sql_agent import SQLAgent

from dotenv import load_dotenv

load_dotenv()

PROJECT = os.environ.get("BRAINTRUST_PROJECT", "agent-evals-workshop")

Eval(
    PROJECT, 
    data=init_dataset(project=PROJECT, name="sql-agent-eval"),
    task=lambda input: SQLAgent().run(input),
    scores=[init_function(project_name=PROJECT, slug="data_eval"),
            init_function(project_name=PROJECT, slug="sql_eval")],
    max_concurrency=5,
)