"""CLI chat interface for the NBA analytics agent."""

from dotenv import load_dotenv

load_dotenv()

from agents.supervisor_agent import SupervisorAgent


def main():
    print("NBA Analytics Chat  |  type 'quit' to exit\n")
    agent = SupervisorAgent()

    while True:
        user_input = input("You >> ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            break

        result = agent.run(user_input)
        print(f"\nAgent >> {result['response']}")
        if result.get("sql_query"):
            print(f"\nSQL query used:\n{result['sql_query']}")
        print()


if __name__ == "__main__":
    main()
