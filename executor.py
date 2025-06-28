# executor.py
import subprocess
import os
import sys
import shlex # Use shlex for safer command splitting
from typing import Tuple, Optional, Callable
from settings import SCRIPTS_DIR

def run_command(command: str, log_func: Optional[Callable[[str], None]] = print) -> Tuple[bool, str]:
    """Runs a shell command safely."""
    if log_func:
        log_func(f"⚙️ 正在执行命令: `{command}`")
    try:
        # shlex.split helps prevent command injection issues
        args = shlex.split(command)
        result = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace', check=False)
        
        output = result.stdout + result.stderr
        if result.returncode == 0:
            if log_func: log_func(f"✅ 命令执行成功。")
            return True, output
        else:
            if log_func: log_func(f"❌ 命令执行失败。")
            return False, output
    except Exception as e:
        if log_func:
            log_func(f"💥 执行命令时发生意外错误: {e}")
        return False, str(e)

# --- run_script function is UNCHANGED, but included for completeness ---
def run_script(script_code: str, script_name: str, log_func: Optional[Callable[[str], None]] = print) -> Tuple[bool, str]:
    if not os.path.exists(SCRIPTS_DIR):
        os.makedirs(SCRIPTS_DIR)
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    try:
        # Always use UTF-8 for writing scripts
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_code)
        if log_func: log_func(f"📜 脚本已保存至: {script_path}")

        if log_func: log_func(f"🚀 正在执行脚本: {script_name}...")
        # Use text=True and encoding='utf-8' for consistent output handling
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,  # Decodes output using 'encoding'
            encoding='utf-8',
            errors='replace', # How to handle decoding errors
            check=False
        )

        if result.returncode == 0:
            if log_func: log_func("✅ 脚本执行成功。")
            return True, result.stdout
        else:
            if log_func: log_func("❌ 脚本执行失败。")
            # Combine stdout and stderr for error context, as errors might print to stdout
            error_output = result.stdout + result.stderr
            return False, error_output if error_output else "脚本执行失败，无输出。"
    except Exception as e:
        if log_func: log_func(f"💥 执行脚本时发生意外错误: {e}")
        return False, str(e)