# error_handler.py
import time
from typing import NamedTuple, Optional, Callable

# 定义一个数据结构来承载修复策略
class FixStrategy(NamedTuple):
    should_retry: bool
    retry_delay: int  # in seconds
    suggestion: str
    error_fingerprint: str # A unique key for this type of error

def analyze_error(e: Exception, log_func: Optional[Callable[[str], None]] = print) -> FixStrategy:
    """
    Analyzes an exception and returns a strategy to handle it.
    """
    error_type = type(e).__name__
    error_message = str(e)
    
    if log_func:
        log_func(f"🕵️‍♂️ Analyzing error: {error_type} - {error_message}")

    # --- Network and API Errors ---
    if isinstance(e, ConnectionError) or "TSI_DATA_CORRUPTED" in error_message:
        return FixStrategy(
            should_retry=True, retry_delay=5,
            suggestion="网络连接错误或SSL问题。将等待5秒后重试...",
            error_fingerprint="network.connection"
        )
    if isinstance(e, TimeoutError):
        return FixStrategy(
            should_retry=True, retry_delay=10,
            suggestion="API请求超时。将等待10秒后重试...",
            error_fingerprint="network.timeout"
        )
    if isinstance(e, ValueError) and ("API Key" in error_message or "model" in error_message):
        return FixStrategy(
            should_retry=False, retry_delay=0,
            suggestion=f"API配置错误: {error_message}。",
            error_fingerprint="config.api"
        )
    if isinstance(e, RuntimeError) and "blocked" in error_message:
        return FixStrategy(
            should_retry=False, retry_delay=0,
            suggestion=f"API请求被拒绝: {error_message}。",
            error_fingerprint="api.blocked"
        )

    # --- Code Execution Errors ---
    if isinstance(e, ChildProcessError):
        # We can make this more granular if needed, e.g., by parsing stderr
        return FixStrategy(
            should_retry=False, # Script errors usually require code changes
            retry_delay=0,
            suggestion="脚本执行失败。未来的版本将尝试调试此错误。",
            error_fingerprint=f"execution.script_error"
        )
    
    # --- Planning and Coding Errors ---
    if "JSONDecodeError" in error_type:
        return FixStrategy(
            should_retry=True, retry_delay=2,
            suggestion="LLM返回的格式无效（非JSON）。将重试...",
            error_fingerprint="llm.output.json"
        )
    if isinstance(e, ValueError) and "Code generation" in error_message:
        return FixStrategy(
            should_retry=True, retry_delay=2,
            suggestion="代码生成或检索失败。将重试...",
            error_fingerprint="agent.code_gen"
        )
    
    # --- Default Catch-all ---
    return FixStrategy(
        should_retry=True, retry_delay=3,
        suggestion=f"遇到未知错误: '{error_message[:100]}...'。将重试。",
        error_fingerprint=f"unknown.{error_type}"
    )