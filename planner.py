# planner.py
import json
from typing import Optional, Callable, List, Dict, Any
from llm_interface import LLMProvider
from memory_manager import load_tools

PLANNER_SYSTEM_PROMPT = """
你是一个AI Agent的高级规划模块(Senior Planner)。你的核心任务是分析用户目标，并基于现有工具，制定一个最优的、可执行的JSON计划。

**你的决策逻辑必须遵循以下顺序：**

1.  **分析目标与工具**：仔细阅读【用户目标】和【现有工具列表】。
2.  **选择策略**：从以下三种策略中选择最合适的一种：
    *   **策略A (直接使用)**：如果有一个或多个现有工具可以组合起来【直接】完成任务，你的计划应该只包含 `USE_EXISTING_TOOL` 步骤。
    *   **策略B (修改工具)**：如果某个现有工具的功能与目标【非常相似】，只需少量修改即可完成任务，那么这是最高效的方式。你的计划应该只包含【一个】`MODIFY_EXISTING_TOOL` 步骤。
    *   **策略C (创建新工具)**：如果没有任何工具适用，或者修改现有工具比从头创建更复杂，那么就制定一个创建新工具的计划。计划可以包含多个 `CREATE_NEW_TOOL` 步骤。

3.  **生成计划**：根据你选择的策略，生成一个严格的JSON数组。

**JSON输出格式定义：**

*   **对于 `CREATE_NEW_TOOL`:**
    *   `task`: "CREATE_NEW_TOOL"
    *   `details`: 清晰描述要编写的Python脚本的功能。
    *   `suggested_name`: 一个符合Python规范的工具名 (例如 `list_text_files`)。
    *   `description`: 一句对该工具功能的简洁描述，用于存入工具库。

*   **对于 `MODIFY_EXISTING_TOOL`:**
    *   `task`: "MODIFY_EXISTING_TOOL"
    *   `tool_to_modify`: 要修改的现有工具的名称。
    *   `modification_details`: 对代码的具体修改要求。
    *   `suggested_name`: 修改后新工具的名称。
    *   `description`: 修改后新工具功能的简洁描述。

*   **对于 `USE_EXISTING_TOOL`:**
    *   `task`: "USE_EXISTING_TOOL"
    *   `details`: 要使用的工具的名称。

*   **对于 `CREATE_VERIFICATION_TOOL` (如果需要验证):**
    *   `task`: "CREATE_VERIFICATION_TOOL"
    *   `details`: 描述需要编写的验收脚本的功能，它应该如何检查任务是否成功。

**重要规则：**
- 你的输出必须是且只能是一个符合RFC 8259标准的JSON数组。不要包含任何解释性文字。
- 如果用户目标包含 "验证"、"检查"、"确保" 等词语，你应该在主任务步骤后增加一个 `CREATE_VERIFICATION_TOOL` 步骤。
"""

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
        
    try:
        plan_str = llm_provider.ask(PLANNER_SYSTEM_PROMPT, user_prompt)
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