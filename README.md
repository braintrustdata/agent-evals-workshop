# Agent Evals Workshop

Build and evaluate a multi-agent eCommerce analytics system with [Braintrust](https://braintrust.dev).

## Architecture

```
User Question
      │
      ▼
┌─────────────┐
│  Supervisor  │  (interprets question, formats response)
│    Agent     │
└──────┬──────┘
       │  ask_sql_agent
       ▼
┌─────────────┐
│  SQL Agent   │  (writes & executes SQL queries)
└──────┬──────┘
       │  run_sql_query / list_tables / describe_table
       ▼
┌─────────────┐
│   SQLite DB  │  (synthetic eCommerce data)
└─────────────┘
```

- **Supervisor Agent** — understands business questions and delegates to the SQL agent
- **SQL Agent** — translates questions into SQL, executes queries, returns results
- **Braintrust AI Proxy** — all LLM calls route through `api.braintrust.dev/v1/proxy` for automatic tracing
- **Braintrust Eval** — offline eval suite with custom scorers

## Prerequisites

- Python 3.10+
- A [Braintrust](https://braintrust.dev) account and API key

## Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/your-org/agent-evals-workshop.git
   cd agent-evals-workshop
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Set up your environment:
   ```bash
   cp .env.example .env
   # Edit .env and add your BRAINTRUST_API_KEY
   ```

4. Generate the synthetic database:
   ```bash
   python setup_db.py
   ```

## Running the agent

Ask any eCommerce analytics question:

```bash
python run_agent.py "How much revenue did we earn last week?"
python run_agent.py "What are the top 3 product categories by revenue last month?"
python run_agent.py "How many customers used the HOLIDAY15 promo code?"
```

Traces appear automatically in [Braintrust Logs](https://www.braintrust.dev).

## Workshop

### Option 1: Online scoring

Run the agent and inspect traces in the Braintrust UI. Add online scorers directly in the Braintrust dashboard to evaluate responses in real time.

### Option 2: Offline eval

Run the full eval suite with custom scorers:

```bash
python run_eval.py
```

This runs 7 eval cases through the agent and scores each with:
- **data_eval** — checks if correct numeric and string values appear in the response
- **sql_eval** — checks structural similarity of the generated SQL vs. reference SQL

Results appear in the Braintrust Experiments view.

## Project structure

```
agent-evals-workshop/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── setup_db.py                  # Generate SQLite DB with synthetic data
├── run_agent.py                 # Invoke agent with a query
├── run_eval.py                  # Run Braintrust eval
├── agents/
│   ├── base_agent.py            # Base agent: OpenAI tool-calling loop + tracing
│   ├── sql_agent.py             # SQL agent with DB tools
│   └── supervisor_agent.py      # Supervisor that delegates to SQL agent
├── tools/
│   └── sql_tools.py             # run_sql_query, list_tables, describe_table
├── eval/
│   ├── dataset.json             # 7 eval cases with ground truth
│   └── scorers.py               # data_eval + sql_eval scorers
├── data/
│   └── ecommerce.db             # Generated SQLite DB (gitignored)
└── prompts/
    ├── supervisor_prompt.py
    └── sql_prompt.py
```

## Sample queries

| Question | What it tests |
|----------|--------------|
| How much revenue did we earn last week? | Date interpretation, SUM aggregation |
| Top 3 product categories by revenue last month? | JOIN, GROUP BY, ORDER BY, LIMIT |
| How many customers used HOLIDAY15? | COUNT DISTINCT, WHERE filter |
| Average order value last month? | AVG aggregation, date range |
| Best-selling book genre? | Subcategory filter, SUM quantity |
| Total discount from all promo codes? | SUM on discount_amount |
| Top 5 states by revenue? | Multi-table JOIN, GROUP BY state |
