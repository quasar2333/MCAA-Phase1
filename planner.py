# planner.py
import json
from typing import Optional, Callable, List, Dict, Any
from llm_interface import LLMProvider
from memory_manager import load_tools
from prompt_engine import prompt_engine_instance # Import the global instance

def create_plan(goal: str, llm_provider: LLMProvider, log_func: Optional[Callable[[str], None]] = print) -> Optional[List[Dict[str, Any]]]:
    """根据用户目标创建计划。"""
    if log_func: log_func("Loading existing tools for planning context...")
    
    existing_tools = load_tools()
    if not existing_tools:
        tools_context = "【现有工具列表】:\n无"
    else:
        formatted_tools = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in existing_tools])
        tools_context = f"【现有工具列表】:\n{formatted_tools}"

    user_prompt = f"{tools_context}\n\n【用户目标】:\n{goal}"

    if log_func: log_func(f"🤖 向 '{llm_provider.get_name()}' 请求规划...")

    planner_prompt = prompt_engine_instance.get_planner_system_prompt()
    try:
        plan_str = llm_provider.ask(planner_prompt, user_prompt)
        if not plan_str:
            return None

        if plan_str.startswith("```json"):
            plan_str = plan_str[7:-3].strip()

        plan = json.loads(plan_str)
        # Add step numbers for clarity
        for i, step in enumerate(plan):
            step['step_number'] = i + 1
        return plan
    except json.JSONDecodeError:
        if log_func:
            log_func("❌ 规划失败：LLM返回的不是有效的JSON格式。")
            log_func(f"LLM原始返回内容:\n---\n{plan_str}\n---")
        return None
    except Exception as e:
        if log_func:
            log_func(f"❌ 规划时发生错误: {e}")
        return None