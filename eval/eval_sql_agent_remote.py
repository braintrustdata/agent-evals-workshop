import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from braintrust import Eval, init_dataset, init_function

from agents.sql_agent import SQLAgent
from prompts.sql_prompt import SQL_SYSTEM_PROMPT

from dotenv import load_dotenv

load_dotenv()

PROJECT = os.environ.get("BRAINTRUST_PROJECT", "agent-evals-workshop")

# Start remote eval server using `braintrust eval eval/eval_sql_agent_remote.py --dev`
# Go playground and select Remote Eval as task

async def task(input, hooks):

    parameters = hooks.parameters
    sql_prompt_param = parameters["sql_prompt"]
    if sql_prompt_param:
        prompt_obj = sql_prompt_param.build()
        sql_prompt = prompt_obj.messages[0]["content"] if hasattr(prompt_obj, "messages") else None
    else:
        sql_prompt = None
    
    agent = SQLAgent(system_prompt=sql_prompt)
    result = agent.run(input)
    
    return result

Eval(   
    PROJECT, 
    data=init_dataset(project=PROJECT, name="sql-agent-eval"),
    task=task,
    scores=[init_function(project_name=PROJECT, slug="data_eval"),
            init_function(project_name=PROJECT, slug="sql_eval")],
    max_concurrency=5,
    parameters={
        "sql_prompt": {
            "type": "prompt",
            "name": "SQL Prompt",
            "description": "System prompt to provide context for SQL queries",
            "default": {
                "prompt": {
                    "type": "chat",
                    "messages": [
                        {
                            "role": "system", 
                            "content": SQL_SYSTEM_PROMPT
                        }
                    ],
                },
                "options": {},
            },
        },
    },
)