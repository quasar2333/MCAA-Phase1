# agent_core.py
import time
import planner
import coder
import executor
import verifier
import memory_manager
from llm_interface import LLMProvider
from typing import Callable, Optional, List, Dict, Any

class Agent:
    def __init__(self, goal: str, llm_provider: LLMProvider, log_func: Callable[[str], None], verify: bool = False):
        self.goal = goal
        self.llm_provider = llm_provider
        self.log = log_func
        self.verify = verify
        self.plan: Optional[List[Dict[str, Any]]] = None

    def run(self):
        """执行Agent的核心任务循环。"""
        self.log("=" * 50)
        self.log(f"🎯 新任务: {self.goal}")
        self.log(f"⚙️ 使用模型: {self.llm_provider.selected_model} @ {self.llm_provider.get_name()}")
        if self.verify: self.log("✅ 自我验证模式已开启")
        self.log("=" * 50)

        # 1. 规划
        plan_goal = self.goal
        if self.verify and "验证" not in plan_goal:
             plan_goal += "\n\n重要：任务完成后，请为任务结果添加一个验证步骤。"
        
        self.plan = planner.create_plan(plan_goal, self.llm_provider, self.log)
        if not self.plan:
            self.log("❌ 无法为该目标创建计划，任务终止。")
            return False

        self.log("\n📑 已生成计划:")
        for step in self.plan:
            self.log(f"  - 步骤 {step['step_number']}: {step['task']} - {step.get('details') or step.get('description') or step.get('tool_to_modify')}")

        # 2. 按计划执行
        for step in self.plan:
            self.log(f"\n--- 正在执行步骤 {step['step_number']}: {step['task']} ---")
            
            script_code = None
            success = False
            output = ""
            
            task_type = step['task']
            
            # 统一处理代码生成/获取
            if task_type == "USE_EXISTING_TOOL":
                tool_name = step['details']
                self.log(f"🔍 正在加载现有工具: '{tool_name}'")
                script_code = memory_manager.get_tool_code(tool_name)
                if not script_code:
                    self.log(f"⚠️ 错误: 工具'{tool_name}'在库中未找到代码。跳过此步骤。")
                    continue
            
            elif task_type == "CREATE_NEW_TOOL":
                script_code = coder.create_code(step['details'], self.llm_provider, self.log)

            elif task_type == "MODIFY_EXISTING_TOOL":
                tool_name = step['tool_to_modify']
                original_code = memory_manager.get_tool_code(tool_name)
                if not original_code:
                    self.log(f"⚠️ 错误: 计划修改的工具'{tool_name}'未找到。转为创建新工具。")
                    script_code = coder.create_code(step['modification_details'], self.llm_provider, self.log)
                else:
                    script_code = coder.modify_code(original_code, step['modification_details'], self.llm_provider, self.log)

            elif task_type == "CREATE_VERIFICATION_TOOL":
                script_code = verifier.create_verification_code(self.goal, step['details'], self.llm_provider, self.log)
            
            else:
                self.log(f"❓ 未知任务类型: {task_type}。跳过。")
                continue

            # 如果代码获取或生成失败，则跳过
            if not script_code:
                self.log(f"❌ 未能获取或生成步骤代码，任务中断。")
                return False

            # 3. 执行
            unique_id = int(time.time() * 1000)
            script_name = f"{step.get('suggested_name', 'tool')}_{unique_id}.py"
            success, output = executor.run_script(script_code, script_name, self.log)

            self.log("执行输出:")
            self.log("-" * 20)
            self.log(output if output else "[无输出]")
            self.log("-" * 20)
            
            if not success:
                self.log("\n‼️ 当前步骤执行失败，任务中断。‼️")
                return False

            # 4. 学习/记忆 (仅对创建和修改成功的工具)
            if task_type in ["CREATE_NEW_TOOL", "MODIFY_EXISTING_TOOL"]:
                self.log("✨ 新工具执行成功！正在自动保存...")
                memory_manager.save_tool(
                    name=step['suggested_name'],
                    description=step['description'],
                    code=script_code,
                    log_func=self.log
                )
        
        self.log("\n🎉 所有步骤执行完毕，任务成功完成！")
        return True
