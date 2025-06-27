# main.py
import argparse
from agent_core import Agent
from llm_interface import get_provider


def main():
    """主函数，运行Agent的命令行交互。"""
    parser = argparse.ArgumentParser(description="MCAA-Phase1: A simple AI Agent")
    parser.add_argument("--provider", help="Name of the API provider from api_config.json", required=True)
    parser.add_argument("--model", help="Specific model to use (optional)", default=None)
    parser.add_argument("--goal", help="The task for the agent to perform", default=None)
    
    args = parser.parse_args()

    llm_provider = get_provider(args.provider)
    if not llm_provider:
        print(f"Error: Provider '{args.provider}' not found in api_config.json.")
        return

    if args.model:
        if args.model not in llm_provider.models:
            print(f"Warning: Model '{args.model}' not listed for provider '{args.provider}'. Attempting to use it anyway.")
        llm_provider.selected_model = args.model

    def cli_log(message: str):
        print(message)

    def cli_input(prompt: str) -> str:
        return input(prompt)

    if args.goal:
        agent = Agent(args.goal, llm_provider, cli_log, cli_input)
        agent.run()
    else:
        print("="*50)
        print("欢迎使用 MCAA-Phase1: 工匠学徒 Agent (CLI模式)")
        print("="*50)
        while True:
            try:
                goal = input("\n请输入你的任务目标 (或输入 'exit' 退出): ")
                if goal.lower() == 'exit':
                    break
                if not goal:
                    continue
                
                agent = Agent(goal, llm_provider, cli_log, cli_input)
                agent.run()

            except KeyboardInterrupt:
                print("\n程序已手动中断。")
                break
            except Exception as e:
                print(f"\n发生未知错误: {e}")

if __name__ == "__main__":
    main()
