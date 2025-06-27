# memory_manager.py
import json
from typing import List, Dict, Any, Callable, Optional

from settings import TOOL_LIBRARY_FILE


def load_tools() -> List[Dict[str, Any]]:
    """从JSON文件中加载所有工具。"""
    try:
        with open(TOOL_LIBRARY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_tool(name: str, description: str, code: str, log_func: Optional[Callable[[str], None]] = print):
    """将一个新工具保存到JSON文件中。"""
    tools = load_tools()
    
    # Sanitize the name to be a valid file/tool name
    safe_name = "".join(c for c in name if c.isalnum() or c in ('_', '-')).rstrip()
    if not safe_name:
        safe_name = f"tool_{hash(description)}"

    # 检查工具是否已存在，如果存在则更新
    for tool in tools:
        if tool['name'] == safe_name:
            tool['description'] = description
            tool['code'] = code
            break
    else:
        tools.append({
            "name": safe_name,
            "description": description,
            "code": code
        })

    with open(TOOL_LIBRARY_FILE, 'w', encoding='utf-8') as f:
        json.dump(tools, f, indent=4, ensure_ascii=False)
    
    if log_func:
        log_func(f"✅ 工具 '{safe_name}' 已成功保存到工具库。")
