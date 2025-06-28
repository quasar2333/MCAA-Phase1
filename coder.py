# coder.py
from typing import Optional, Callable
from llm_interface import LLMProvider
from prompt_engine import prompt_engine_instance # Import the global instance

def create_code(task_description: str, llm_provider: LLMProvider, log_func: Optional[Callable[[str], None]] = print) -> Optional[str]:
    """根据任务描述生成Python代码。"""
    if log_func: log_func(f"🤖 正在为任务 '{task_description}' 请求 '{llm_provider.get_name()}' 生成代码...")
    
    coder_prompt = prompt_engine_instance.get_coder_system_prompt()
    try:
        code = llm_provider.ask(coder_prompt, task_description)
        return _clean_code(code, log_func)
    except Exception as e:
        if log_func: log_func(f"❌ 代码生成时发生错误: {e}")
        return None

def modify_code(original_code: str, modification_request: str, llm_provider: LLMProvider, log_func: Optional[Callable[[str], None]] = print) -> Optional[str]:
    """根据请求修改现有代码。"""
    if log_func: log_func(f"🤖 正在根据请求 '{modification_request}' 修改现有代码...")

    user_prompt = f"【现有代码】:\n```python\n{original_code}\n```\n\n【修改要求】:\n{modification_request}"
    modifier_prompt = prompt_engine_instance.get_modifier_system_prompt()
    
    try:
        code = llm_provider.ask(modifier_prompt, user_prompt)
        return _clean_code(code, log_func)
    except Exception as e:
        if log_func: log_func(f"❌ 代码修改时发生错误: {e}")
        return None

def _clean_code(code: Optional[str], log_func: Optional[Callable[[str], None]] = print) -> Optional[str]:
    """清理LLM返回的代码，移除markdown等。"""
    if not code:
        return None
    
    if code.startswith("```python"):
        code = code[9:-3].strip()
    elif code.startswith("```"):
        code = code[3:-3].strip()

    if "Traceback" in code:
        if log_func: log_func(f"❌ 代码生成失败或返回了错误: {code}")
        return None
        
    return code