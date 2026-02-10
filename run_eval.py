"""Run Braintrust eval for the eCommerce analytics agent."""

import json
import os

from dotenv import load_dotenv

load_dotenv()

import braintrust

from agents.supervisor_agent import SupervisorAgent
from eval.scorers import data_eval, sql_eval


def load_dataset():
    dataset_path = os.path.join(os.path.dirname(__file__), "eval", "dataset.json")
    with open(dataset_path) as f:
        return json.load(f)


def task(input: str, hooks=None) -> dict:
    agent = SupervisorAgent()
    result = agent.run(input)
    return result


def run():
    braintrust.Eval(
        "agent-evals-workshop",
        data=load_dataset,
        task=task,
        scores=[data_eval, sql_eval],
    )


if __name__ == "__main__":
    run()
