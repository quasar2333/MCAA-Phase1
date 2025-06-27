# coder.py
from typing import Optional, Callable
from llm_interface import LLMProvider

CODER_SYSTEM_PROMPT = """
你是一位顶级的Python编程专家。你的任务是根据用户的需求，编写一段完整、可直接运行的Python脚本。
- 你的代码必须是独立的，所有必要的导入都应包含在内。
- 不要使用任何需要额外安装的、不常见的第三方库，尽量使用Python标准库。
- 你的输出必须是且只能是纯粹的Python代码。不要包含任何注释、解释、或Markdown标记如 ```python。
- 代码必须是高质量、健壮的，并处理常见的异常情况。
"""

def create_code(task_description: str, llm_provider: LLMProvider, log_func: Optional[Callable[[str], None]] = print) -> Optional[str]:
    """根据任务描述生成Python代码。"""
    if log_func:
        log_func(f"🤖 正在为任务 '{task_description}' 请求 '{llm_provider.get_name()}' 生成代码...")
    
    try:
        code = llm_provider.ask(CODER_SYSTEM_PROMPT, task_description)
        
        # Clean potential markdown code blocks
        if code and code.startswith("```python"):
            code = code[9:-3].strip()
        
        if not code or "Traceback" in code:
            if log_func:
                log_func(f"❌ 代码生成失败或返回了错误: {code}")
            return None
        return code
    except Exception as e:
        if log_func:
            log_func(f"❌ 代码生成时发生错误: {e}")
        return None
