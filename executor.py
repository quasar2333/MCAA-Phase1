# executor.py
import subprocess
import os

SCRIPTS_DIR = 'generated_scripts'

def run_script(script_code: str, script_name: str) -> (bool, str):
    """
    将代码保存为脚本文件并执行。
    返回一个元组 (是否成功, 输出或错误信息)。
    """
    # 确保存放脚本的目录存在
    if not os.path.exists(SCRIPTS_DIR):
        os.makedirs(SCRIPTS_DIR)

    script_path = os.path.join(SCRIPTS_DIR, script_name)

    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_code)
        print(f"脚本已保存至: {script_path}")

        # 【警告】这里直接执行代码，存在巨大安全风险！
        print(f"正在执行脚本: {script_name}...")
        result = subprocess.run(
            ['python', script_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=False # 设置为False，这样即使脚本出错也不会抛出异常
        )

        if result.returncode == 0:
            print("脚本执行成功。")
            return True, result.stdout
        else:
            print("脚本执行失败。")
            error_message = result.stderr
            return False, error_message

    except Exception as e:
        print(f"执行脚本时发生意外错误: {e}")
        return False, str(e)
