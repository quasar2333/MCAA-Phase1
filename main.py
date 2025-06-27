# main.py
import planner
import coder
import executor
import memory_manager
import time
import argparse
from config import DEFAULT_PROVIDER

def main(provider_name: str = DEFAULT_PROVIDER):
    """主函数，运行Agent的交互循环。"""
    print("="*50)
    print("欢迎使用 MCAA-Phase1: 工匠学徒 Agent")
    print("="*50)

    while True:
        try:
            goal = input("\n请输入你的任务目标 (或输入 'exit' 退出): ")
            if goal.lower() == 'exit':
                break

            # 1. 规划
            plan = planner.create_plan(goal, provider_name)
            if not plan:
                print("无法为该目标创建计划，请尝试更清晰的描述。")
                continue

            print("\n已生成计划:")
            for step in plan:
                print(f"  - 步骤 {step['step_number']}: {step['task']} - {step['details']}")

            # 2. 按计划执行
            for step in plan:
                print(f"\n--- 正在执行步骤 {step['step_number']}: {step['task']} ---")
                task_type = step['task']
                details = step['details']

                script_code = ""
                tool_name = ""

                if task_type == "USE_EXISTING_TOOL":
                    tool_name = details
                    tools = memory_manager.load_tools()
                    found_tool = next((t for t in tools if t['name'] == tool_name), None)
                    if found_tool:
                        print(f"找到现有工具: '{tool_name}'")
                        script_code = found_tool['code']
                    else:
                        print(f"错误: 计划使用工具'{tool_name}'，但在库中未找到。跳过此步骤。")
                        continue

                elif task_type == "CREATE_NEW_TOOL":
                    script_code = coder.create_code(details, provider_name)
                    if not script_code or "Traceback" in script_code:
                        print(f"代码生成失败: {script_code}")
                        continue

                # 3. 执行
                script_name = f"{tool_name or 'temp_tool'}_{int(time.time())}.py"
                success, output = executor.run_script(script_code, script_name)

                print("执行输出:")
                print(output)

                # 4. 学习/记忆
                if success and task_type == "CREATE_NEW_TOOL":
                    print("\n新工具执行成功！")
                    save_choice = input("是否要将这个新工具保存到你的工具库? (y/n): ").lower()
                    if save_choice == 'y':
                        new_tool_name = input("请输入新工具的名称 (例如 'create_folder'): ")
                        memory_manager.save_tool(new_tool_name, details, script_code)

                if not success:
                    print("\n！！！！！！！！！！！！！！！！！！！！！！")
                    print("当前步骤执行失败，任务中断。")
                    print("（在未来版本中，这里将触发调试循环）")
                    print("！！！！！！！！！！！！！！！！！！！！！！")
                    break # 中断当前任务

            print("\n所有步骤执行完毕，任务完成！")

        except KeyboardInterrupt:
            print("\n程序已手动中断。")
            break
        except Exception as e:
            print(f"\n发生未知错误: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the MCAA agent")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER, help="API provider name to use")
    args = parser.parse_args()
    main(args.provider)
