import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from braintrust import Eval, init_dataset, init_function

from agents.sql_agent import SQLAgent

Eval(
    "agent-evals-workshop", 
    data=init_dataset(project="agent-evals-workshop", name="sql-agent-eval"),
    task=lambda input: SQLAgent().run(input),
    scores=[init_function(project_name="agent-evals-workshop", slug="data_eval"),
            init_function(project_name="agent-evals-workshop", slug="sql_eval")],
    max_concurrency=5,
)