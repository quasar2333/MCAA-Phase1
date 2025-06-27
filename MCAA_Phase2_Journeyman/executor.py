# executor.py
import subprocess
import os
from typing import Tuple, Optional, Callable
from settings import SCRIPTS_DIR

def run_script(script_code: str, script_name: str, log_func: Optional[Callable[[str], None]] = print) -> Tuple[bool, str]:
    if not os.path.exists(SCRIPTS_DIR):
        os.makedirs(SCRIPTS_DIR)

    script_path = os.path.join(SCRIPTS_DIR, script_name)

    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_code)
        if log_func: log_func(f"📜 脚本已保存至: {script_path}")

        if log_func: log_func(f"🚀 正在执行脚本: {script_name}...")
        
        result = subprocess.run(
            ['python', script_path],
            capture_output=True, text=True, encoding='utf-8', check=False
        )

        if result.returncode == 0:
            if log_func: log_func("✅ 脚本执行成功。")
            return True, result.stdout
        else:
            if log_func: log_func("❌ 脚本执行失败。")
            return False, result.stderr
    except Exception as e:
        if log_func: log_func(f"💥 执行脚本时发生意外错误: {e}")
        return False, str(e)
