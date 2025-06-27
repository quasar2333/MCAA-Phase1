# verifier.py
from typing import Optional, Callable
from llm_interface import LLMProvider
from coder import _clean_code

VERIFIER_SYSTEM_PROMPT = """
你是一名高级软件质量保证(QA)工程师。你的任务是为一段Python代码编写一个验收测试脚本。
这个测试脚本本身也必须是可独立运行的Python脚本。

**你的任务：**
根据【原始目标】和【已执行的代码】，编写一个独立的Python验收脚本来验证任务是否成功。

**验收脚本要求：**
1.  使用Python标准库。
2.  使用 `assert` 语句或抛出异常来进行检查。
3.  如果检查通过，脚本应该正常退出（返回码0）。
4.  如果检查失败，脚本应该因为断言失败或未捕获的异常而退出（返回码非0）。
5.  你的输出必须是且只能是纯粹的Python代码，不含任何解释。
"""

def create_verification_code(
    original_goal: str, 
    executed_code_description: str,
    llm_provider: LLMProvider, 
    log_func: Optional[Callable[[str], None]] = print
) -> Optional[str]:
    """生成用于验证任务是否成功的代码。"""
    if log_func: log_func("🤖 正在生成验收测试脚本...")

    user_prompt = f"【原始目标】: {original_goal}\n\n【任务描述】: {executed_code_description}\n\n请编写验收测试脚本。"

    try:
        code = llm_provider.ask(VERIFIER_SYSTEM_PROMPT, user_prompt)
        return _clean_code(code, log_func)
    except Exception as e:
        if log_func:
            log_func(f"❌ 验收代码生成时发生错误: {e}")
        return None
