# memory_manager.py
import json
from typing import List, Dict, Any, Callable, Optional
import time
from settings import TOOL_LIBRARY_FILE

def load_tools() -> List[Dict[str, Any]]:
    """从JSON文件中加载所有工具。"""
    try:
        with open(TOOL_LIBRARY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def get_tool_code(tool_name: str) -> Optional[str]:
    """获取单个工具的代码。"""
    tools = load_tools()
    for tool in tools:
        if tool['name'] == tool_name:
            return tool.get('code')
    return None

def save_tool(name: str, description: str, code: str, log_func: Optional[Callable[[str], None]] = print):
    """将一个新工具保存到JSON文件中，自动处理命名冲突。"""
    tools = load_tools()
    
    # Sanitize the name to be a valid file/tool name
    base_name = "".join(c for c in name if c.isalnum() or c in ('_', '-')).rstrip()
    if not base_name:
        base_name = f"unnamed_tool"

    final_name = base_name
    # 检查工具是否已存在，如果存在则更新或重命名
    existing_tool = next((t for t in tools if t['name'] == final_name), None)

    if existing_tool:
        # 如果代码完全相同，则不保存
        if existing_tool['code'] == code:
            if log_func:
                log_func(f"ℹ️ 工具 '{final_name}' 已存在且代码相同，无需保存。")
            return
        # 如果代码不同，则添加后缀
        final_name = f"{base_name}_{int(time.time())}"
        if log_func:
            log_func(f"⚠️ 工具名 '{base_name}' 已存在，新工具将保存为 '{final_name}'。")
    
    # Append the new or renamed tool
    tools.append({
        "name": final_name,
        "description": description,
        "code": code
    })

    with open(TOOL_LIBRARY_FILE, 'w', encoding='utf-8') as f:
        json.dump(tools, f, indent=4, ensure_ascii=False)
    
    if log_func:
        log_func(f"✅ 工具 '{final_name}' 已成功保存到工具库。")