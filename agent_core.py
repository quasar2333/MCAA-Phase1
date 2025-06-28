# agent_core.py
import time
from collections import defaultdict
import planner
import coder
import executor
import verifier
import memory_manager
import error_handler
import diagnostician # NEW
from llm_interface import LLMProvider
from typing import Callable, Optional, List, Dict, Any

class Agent:
    # ... __init__ and _execute_with_retry are the same as before ...
    def __init__(self, goal: str, llm_provider: LLMProvider, log_func: Callable[[str], None], verify: bool = False, previous_context: Optional[Dict] = None):
        self.goal = goal
        self.llm_provider = llm_provider
        self.log = log_func
        self.verify = verify
        self.previous_context = previous_context
        self.plan: Optional[List[Dict[str, Any]]] = None
        self.max_retries = 3
        self.final_code_for_step = {}
        self.failure_reason = ""

    def _execute_with_retry(self, func, *args, **kwargs):
        # ... (unchanged)
        error_counts = defaultdict(int)
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                strategy = error_handler.analyze_error(e, self.log)
                error_fingerprint = strategy.error_fingerprint
                error_counts[error_fingerprint] += 1
                self.log(f"💡 错误处理策略: {strategy.suggestion}")
                if error_counts[error_fingerprint] >= self.max_retries:
                    self.log(f"‼️ 错误 '{error_fingerprint}' 重复出现 {self.max_retries} 次，终止当前操作。")
                    raise e
                if strategy.should_retry:
                    if strategy.retry_delay > 0:
                        self.log(f"⏳ 等待 {strategy.retry_delay} 秒...")
                        time.sleep(strategy.retry_delay)
                    self.log(f"🔄 正在重试 (尝试 {error_counts[error_fingerprint] + 1}/{self.max_retries})...")
                else:
                    raise e

    def run(self) -> bool:
        """The main agent loop, now with a meta-level diagnostic loop."""
        try:
            # The primary execution flow
            return self._run_primary_task()
        except Exception as fatal_error:
            # If the primary flow fails with a fatal error, start diagnostics
            self.log("\n" + "="*20 + " 致命错误 " + "="*20)
            self.log(f"💥 Agent遇到无法恢复的错误，正在启动诊断... 错误详情: {fatal_error}")
            self.log("="*53)
            
            # Construct context for the diagnostician
            context = {
                "goal": self.goal,
                "failed_step": self.last_failed_step if hasattr(self, 'last_failed_step') else "N/A",
                "error_log": str(fatal_error)
            }
            
            repair_plan = diagnostician.diagnose_and_plan(context, self.llm_provider, self.log)
            
            if not repair_plan:
                self.log("❌ 诊断失败，无法生成修复计划。任务彻底终止。")
                return False

            if repair_plan.get("strategy") == "ATTEMPT_SELF_REPAIR":
                self.log("🛠️ 正在尝试自我修复...")
                repair_success = self._execute_repair_plan(repair_plan['plan'])
                if repair_success:
                    self.log("✅ 自我修复成功！正在重试原始任务...")
                    # After successful repair, try the whole task again
                    return self._run_primary_task()
                else:
                    self.log("❌ 自我修复失败。任务终止。")
                    return False
            elif repair_plan.get("strategy") == "REQUEST_USER_INTERVENTION":
                instructions = repair_plan['plan'][0]['instructions_for_user']
                self.log("\n" + "🤚" * 20)
                self.log("‼️ Agent无法自行解决此问题，需要您的帮助！‼️")
                self.log("【操作指南】:")
                self.log(instructions)
                self.log("🤚" * 20)
                return False
            else:
                self.log("❓ 未知的诊断策略。任务终止。")
                return False

    def _run_primary_task(self) -> bool:
        """The original task execution logic."""
        self.log("=" * 50)
        # ... (This block is the same as the old run() method)
        if self.previous_context and self.previous_context.get("modification_request"):
            self.log(f"🚀 继续任务: {self.previous_context['original_goal']}")
            self.log(f"📝 新要求: {self.previous_context['modification_request']}")
        else:
            self.log(f"🎯 新任务: {self.goal}")
        
        self.log(f"⚙️ 使用模型: {self.llm_provider.selected_model} @ {self.llm_provider.get_name()}")
        if self.verify: self.log("✅ 自我验证模式已开启")
        self.log("=" * 50)
        # End of unchanged block

        plan_goal = self._prepare_planning_goal()
        self.plan = self._execute_with_retry(planner.create_plan, plan_goal, self.llm_provider, self.log)
        if not self.plan:
            raise Exception("无法创建计划。") # Let the outer loop handle this

        self.log("\n📑 已生成计划:")
        for step in self.plan:
            self.log(f"  - {step['step_number']}: {step['task']} - {step.get('details') or step.get('description') or step.get('tool_to_modify')}")
        
        for step in self.plan:
            self.last_failed_step = step # Store context in case of failure
            self.log(f"\n--- 正在执行步骤 {step['step_number']}: {step['task']} ---")
            self._execute_step(step)

        self.log("\n🎉 所有步骤执行完毕，任务成功完成！")
        return True
    
    def _execute_repair_plan(self, plan: List[Dict[str, Any]]) -> bool:
        """Executes the steps from the diagnostician's plan."""
        for step in plan:
            self.log(f"--- 正在执行修复步骤: {step['description']} ---")
            task_type = step['task']
            success = False
            
            if task_type == "RUN_COMMAND":
                success, output = executor.run_command(step['command'], self.log)
                self.log(f"命令输出:\n{output}")
            elif task_type == "WRITE_AND_EXECUTE_SCRIPT":
                code = coder.create_code(step['details'], self.llm_provider, self.log)
                if code:
                    success, output = executor.run_script(code, "repair_script.py", self.log)
                    self.log(f"修复脚本输出:\n{output}")
            
            if not success:
                self.log(f"❌ 修复步骤 '{step['description']}' 失败。")
                return False
        return True

    # _prepare_planning_goal, _execute_step, _get_code_for_step, _get_code_for_step_logic are all unchanged
    # ...
    def _prepare_planning_goal(self) -> str:
        if not self.previous_context:
            plan_goal = self.goal
            if self.verify and "验证" not in plan_goal:
                plan_goal += "\n\n重要：任务完成后，请为任务结果添加一个验证步骤。"
            return plan_goal
        else:
            ctx = self.previous_context
            context_prompt = (
                f"你正在一个迭代任务中。这是上一次任务的上下文：\n"
                f"【原始目标】: {ctx['original_goal']}\n"
                f"【上次失败原因】(如果有): {ctx.get('failure_reason', '无')}\n"
                f"【上次生成的代码】:\n```python\n{ctx.get('last_code', '# 无代码')}\n```\n\n"
                f"现在，用户提出了新的要求：\n"
                f"【新修改要求】: {ctx['modification_request']}\n\n"
                "请基于以上所有信息，生成一个新的计划来满足用户的修改要求。优先考虑使用 MODIFY_EXISTING_TOOL。"
            )
            return context_prompt

    def _execute_step(self, step: Dict[str, Any]):
        script_code = self._get_code_for_step(step)
        step_number = step['step_number']
        self.final_code_for_step[step_number] = script_code
        if not script_code:
            raise ValueError("Code generation or retrieval failed for the step.")
        unique_id = int(time.time() * 1000)
        script_name = f"{step.get('suggested_name', 'tool')}_{unique_id}.py"
        success, output = executor.run_script(script_code, script_name, self.log)
        self.log("执行输出:\n" + "-" * 20 + f"\n{output if output else '[无输出]'}\n" + "-" * 20)
        if not success:
            self.failure_reason = output
            raise ChildProcessError(f"脚本执行失败。")
        if step['task'] in ["CREATE_NEW_TOOL", "MODIFY_EXISTING_TOOL"]:
            self.log("✨ 新工具执行成功！正在自动保存...")
            memory_manager.save_tool(step['suggested_name'], step['description'], script_code, self.log)

    def _get_code_for_step(self, step: Dict[str, Any]) -> Optional[str]:
        return self._execute_with_retry(self._get_code_for_step_logic, step)

    def _get_code_for_step_logic(self, step: Dict[str, Any]) -> Optional[str]:
        task_type = step['task']
        if task_type == "USE_EXISTING_TOOL":
            tool_name = step['details']
            self.log(f"🔍 正在加载现有工具: '{tool_name}'")
            return memory_manager.get_tool_code(tool_name)
        elif task_type == "CREATE_NEW_TOOL":
            return coder.create_code(step['details'], self.llm_provider, self.log)
        elif task_type == "MODIFY_EXISTING_TOOL":
            tool_name = step['tool_to_modify']
            original_code = self.previous_context.get('last_code') if self.previous_context else memory_manager.get_tool_code(tool_name)
            if not original_code:
                self.log(f"⚠️ 计划修改的工具'{tool_name}'未找到。转为创建新工具。")
                return coder.create_code(step['modification_details'], self.llm_provider, self.log)
            else:
                return coder.modify_code(original_code, step['modification_details'], self.llm_provider, self.log)
        elif task_type == "CREATE_VERIFICATION_TOOL":
            return verifier.create_verification_code(self.goal, step['details'], self.llm_provider, self.log)
        self.log(f"❓ 未知任务类型: {task_type}。")
        return None