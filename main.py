# main.py
import argparse
from agent_core import Agent
from llm_interface import get_provider
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from dotenv import load_dotenv

# Load environment variables from .env file at the beginning
load_dotenv()

console = Console()

def main():
    parser = argparse.ArgumentParser(description="MCAA-Phase2: The Journeyman Agent - CLI")
    parser.add_argument("--provider", help="Name of the API provider from api_config.json", required=True)
    parser.add_argument("--model", help="Specific model to use (optional)", default=None)
    parser.add_argument("--goal", help="The task for the agent to perform", default=None)
    parser.add_argument("--verify", action='store_true', help="Enable self-verification mode")
    
    args = parser.parse_args()

    llm_provider = get_provider(args.provider)
    if not llm_provider:
        console.print(f"[bold red]错误：[/bold red]在 api_config.json 中未找到提供者 '{args.provider}'。")
        return

    if args.model:
        if args.model not in llm_provider.models:
            console.print(f"[yellow]警告：[/yellow]模型 '{args.model}' 未在配置中列出，将尝试继续使用。")
        llm_provider.selected_model = args.model

    def cli_log(message: str):
        # Simple heuristic to style messages based on content
        if message.startswith("✅") or message.startswith("🎉"):
            console.print(Text(message, style="green"))
        elif message.startswith("❌") or message.startswith("💥") or "错误" in message or "失败" in message :
            console.print(Text(message, style="red"))
        elif message.startswith("⚠️") or message.startswith("💡") or message.startswith("⏳") or message.startswith("🔄"):
            console.print(Text(message, style="yellow"))
        elif message.startswith("⚙️") or message.startswith("📜") or message.startswith("🚀") or message.startswith("🤖") or message.startswith("🤔"):
            console.print(Text(message, style="blue"))
        elif message.startswith("📑") or message.startswith("---") or message.startswith("==="):
            console.print(Text(message, style="bold magenta"))
        else:
            console.print(message)

    if args.goal:
        agent = Agent(args.goal, llm_provider, cli_log, args.verify)
        agent.run()
    else:
        console.print(Panel("[bold cyan]欢迎使用 MCAA-Phase2: 熟练工匠 Agent (CLI模式)[/bold cyan]", expand=False, border_style="dim cyan"))
        while True:
            try:
                goal = console.input("\n[bold spring_green2]请输入你的任务目标[/bold spring_green2] (或输入 '[cyan]exit[/cyan]' 退出): ")
                if goal.lower() == 'exit':
                    break
                if not goal:
                    continue
                
                verify_choice = console.input("[bold spring_green2]是否开启自我验证模式?[/bold spring_green2] (y/n): ").lower()
                agent = Agent(goal, llm_provider, cli_log, verify_choice == 'y')
                agent.run()

            except KeyboardInterrupt:
                console.print("\n[yellow]程序已手动中断。[/yellow]")
                break
            except Exception as e:
                console.print(f"\n[bold red]发生未知错误:[/bold red] {e}")
                console.print_exception(show_locals=True) # For more detailed error info

if __name__ == "__main__":
    main()