# agent_core.py
import time
import planner
import coder
import executor
import memory_manager
from llm_interface import LLMProvider
from typing import Callable, Optional, List, Dict, Any


class Agent:
    def __init__(self, goal: str, llm_provider: LLMProvider, log_func: Callable[[str], None], input_func: Callable[[str], str]):
        self.goal = goal
        self.llm_provider = llm_provider
        self.log = log_func
        self.ask_user = input_func
        self.plan: Optional[List[Dict[str, Any]]] = None

    def run(self):
        """执行Agent的核心任务循环。"""
        self.log("=" * 50)
        self.log(f"🎯 新任务: {self.goal}")
        self.log(f"⚙️ 使用模型: {self.llm_provider.selected_model} @ {self.llm_provider.get_name()}")
        self.log("=" * 50)

        # 1. 规划
        self.plan = planner.create_plan(self.goal, self.llm_provider, self.log)
        if not self.plan:
            self.log("❌ 无法为该目标创建计划，任务终止。")
            return

        self.log("\n📑 已生成计划:")
        for step in self.plan:
            self.log(f"  - 步骤 {step['step_number']}: {step['task']} - {step['details']}")

        # 2. 按计划执行
        for step in self.plan:
            self.log(f"\n--- 正在执行步骤 {step['step_number']}: {step['task']} ---")
            task_type = step['task']
            details = step['details']

            script_code = ""
            tool_name = ""

            if task_type == "USE_EXISTING_TOOL":
                tool_name = details
                tools = memory_manager.load_tools()
                found_tool = next((t for t in tools if t['name'] == tool_name), None)
                if found_tool:
                    self.log(f"🔍 找到现有工具: '{tool_name}'")
                    script_code = found_tool['code']
                else:
                    self.log(f"⚠️ 错误: 计划使用工具'{tool_name}'，但在库中未找到。跳过此步骤。")
                    continue

            elif task_type == "CREATE_NEW_TOOL":
                script_code = coder.create_code(details, self.llm_provider, self.log)
                if not script_code:
                    self.log("❌ 代码生成失败，跳过此步骤。")
                    continue

            # 3. 执行
            # Generate a unique name for the script file
            unique_id = int(time.time() * 1000)
            script_name = f"{tool_name or 'temp_tool'}_{unique_id}.py"
            success, output = executor.run_script(script_code, script_name, self.log)

            self.log("执行输出:")
            self.log("-" * 20)
            self.log(output if output else "[无输出]")
            self.log("-" * 20)

            # 4. 学习/记忆
            if success and task_type == "CREATE_NEW_TOOL":
                self.log("\n✨ 新工具执行成功！")
                save_choice = self.ask_user("是否要将这个新工具保存到你的工具库? (y/n): ").lower()
                if save_choice == 'y':
                    new_tool_name = self.ask_user("请输入新工具的名称 (例如 'create_folder'): ")
                    if new_tool_name:
                        memory_manager.save_tool(new_tool_name, details, script_code, self.log)
                    else:
                        self.log("未提供名称，工具未保存。")

            if not success:
                self.log("\n‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️")
                self.log("当前步骤执行失败，任务中断。")
                self.log("（在未来版本中，这里将触发调试循环）")
                self.log("‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️")
                return

        self.log("\n🎉 所有步骤执行完毕，任务成功完成！")
