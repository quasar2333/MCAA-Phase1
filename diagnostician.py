# diagnostician.py
import json
from typing import Dict, Any, Optional, Callable
from llm_interface import LLMProvider

DIAGNOSTICIAN_SYSTEM_PROMPT = """
你是一个AI Agent的首席系统诊断工程师。Agent在执行任务时遇到了一个无法通过代码重试解决的根本性错误。你的任务是分析整个失败上下文，并制定一个【系统级修复计划】。

【失败上下文】会包含：
- 初始用户目标
- 失败步骤的计划
- 完整的终端错误日志（stderr）

你的输出必须是一个严格的JSON对象，包含以下字段：
1. "root_cause_analysis": (string) 你对根本原因的分析，用简洁的技术语言描述。例如："SSL解密失败，表明存在网络中间人或代理拦截。"
2. "strategy": (string) 从以下策略中选择一个：["ATTEMPT_SELF_REPAIR", "REQUEST_USER_INTERVENTION"]
3. "plan": (array) 一个详细的修复步骤列表。

【修复计划（plan）的步骤格式】
- 如果 strategy 是 "ATTEMPT_SELF_REPAIR":
  - 步骤可以是 "RUN_COMMAND" 或 "WRITE_AND_EXECUTE_SCRIPT"。
  - "RUN_COMMAND": {"task": "RUN_COMMAND", "command": "pip install --upgrade certifi", "description": "描述此命令的目的"}
  - "WRITE_AND_EXECUTE_SCRIPT": {"task": "WRITE_AND_EXECUTE_SCRIPT", "details": "编写脚本的功能描述", "description": "描述此脚本的目的"}
- 如果 strategy 是 "REQUEST_USER_INTERVENTION":
  - 步骤只有一个 "REQUEST_USER_ACTION"。
  - "REQUEST_USER_ACTION": {"task": "REQUEST_USER_ACTION", "instructions_for_user": "给用户的清晰操作指南。"}

【示例分析】
输入上下文: 
{ 
  "goal": "获取电脑配置", 
  "failed_step": "{...}", 
  "error_log": "SSL DECRYPTION FAILED..." 
}
输出JSON:
{
  "root_cause_analysis": "SSL/TLS解密失败，极有可能是由于网络代理或防火墙拦截了HTTPS流量。",
  "strategy": "ATTEMPT_SELF_REPAIR",
  "plan": [
    {
      "task": "RUN_COMMAND",
      "command": "pip install --upgrade certifi",
      "description": "第一步：尝试更新证书库，这可能解决部分问题。"
    },
    {
      "task": "WRITE_AND_EXECUTE_SCRIPT",
      "details": "编写一个Python脚本，使用os模块检查HTTPS_PROXY和HTTP_PROXY环境变量是否存在并打印它们的值。",
      "description": "第二步：检查系统是否已配置代理环境变量，为后续诊断提供信息。"
    }
  ]
}
"""

def diagnose_and_plan(
    context: Dict[str, Any], 
    llm_provider: LLMProvider, 
    log_func: Optional[Callable[[str], None]] = print
) -> Optional[Dict[str, Any]]:
    """Analyzes a fatal error and creates a repair plan."""
    if log_func:
        log_func("🤔 遇到致命错误，启动首席诊断工程师...")
        log_func(f"上下文: {context}")

    user_prompt = f"请分析以下失败上下文并制定修复计划:\n\n{json.dumps(context, indent=2)}"

    try:
        response_str = llm_provider.ask(DIAGNOSTICIAN_SYSTEM_PROMPT, user_prompt)
        if not response_str:
            return None
        
        # Clean potential markdown
        if response_str.startswith("```json"):
            response_str = response_str[7:-3].strip()
            
        repair_plan = json.loads(response_str)
        if log_func:
            log_func(f"ախ 诊断报告与修复计划已生成:")
            log_func(json.dumps(repair_plan, indent=2, ensure_ascii=False))
        return repair_plan
    except Exception as e:
        if log_func:
            log_func(f"💥 诊断模块本身发生错误: {e}")
        return None