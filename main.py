# main.py
import argparse
from agent_core import Agent
from llm_interface import get_provider

def main():
    parser = argparse.ArgumentParser(description="MCAA-Phase2: The Journeyman Agent")
    parser.add_argument("--provider", help="Name of the API provider from api_config.json", required=True)
    parser.add_argument("--model", help="Specific model to use (optional)", default=None)
    parser.add_argument("--goal", help="The task for the agent to perform", default=None)
    parser.add_argument("--verify", action='store_true', help="Enable self-verification mode")
    
    args = parser.parse_args()

    llm_provider = get_provider(args.provider)
    if not llm_provider:
        print(f"错误：在 api_config.json 中未找到提供者 '{args.provider}'。")
        return

    if args.model:
        if args.model not in llm_provider.models:
            print(f"警告：模型 '{args.model}' 未在配置中列出，将尝试继续使用。")
        llm_provider.selected_model = args.model

    def cli_log(message: str):
        print(message)

    if args.goal:
        agent = Agent(args.goal, llm_provider, cli_log, args.verify)
        agent.run()
    else:
        print("="*50)
        print("欢迎使用 MCAA-Phase2: 熟练工匠 Agent (CLI模式)")
        print("="*50)
        while True:
            try:
                goal = input("\n请输入你的任务目标 (或输入 'exit' 退出): ")
                if goal.lower() == 'exit': break
                if not goal: continue
                
                verify_choice = input("是否开启自我验证模式? (y/n): ").lower()
                agent = Agent(goal, llm_provider, cli_log, verify_choice == 'y')
                agent.run()

            except KeyboardInterrupt:
                print("\n程序已手动中断。")
                break
            except Exception as e:
                print(f"\n发生未知错误: {e}")

if __name__ == "__main__":
    main()