# executor.py
import subprocess
import os
from typing import Tuple, Optional, Callable

from settings import SCRIPTS_DIR


def run_script(script_code: str, script_name: str, log_func: Optional[Callable[[str], None]] = print) -> Tuple[bool, str]:
    """
    将代码保存为脚本文件并执行。
    返回一个元组 (是否成功, 输出或错误信息)。
    """
    if not os.path.exists(SCRIPTS_DIR):
        os.makedirs(SCRIPTS_DIR)

    script_path = os.path.join(SCRIPTS_DIR, script_name)

    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_code)
        if log_func:
            log_func(f"📜 脚本已保存至: {script_path}")

        if log_func:
            log_func(f"🚀 正在执行脚本: {script_name}...")
        
        # 【警告】这里直接执行代码，存在巨大安全风险！
        result = subprocess.run(
            ['python', script_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=False
        )

        if result.returncode == 0:
            if log_func:
                log_func("✅ 脚本执行成功。")
            return True, result.stdout
        else:
            if log_func:
                log_func("❌ 脚本执行失败。")
            error_message = result.stderr
            return False, error_message

    except Exception as e:
        if log_func:
            log_func(f"💥 执行脚本时发生意外错误: {e}")
        return False, str(e)
