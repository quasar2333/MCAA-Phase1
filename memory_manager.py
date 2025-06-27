# memory_manager.py
import json
from typing import List, Dict, Any

TOOL_LIBRARY_FILE = 'tool_library.json'

def load_tools() -> List[Dict[str, Any]]:
    """从JSON文件中加载所有工具。"""
    try:
        with open(TOOL_LIBRARY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # 如果文件不存在或为空，返回一个空列表
        return []

def save_tool(name: str, description: str, code: str, log_func=print):
    """将一个新工具保存到JSON文件中。"""
    tools = load_tools()
    # 检查工具是否已存在，如果存在则更新
    for tool in tools:
        if tool['name'] == name:
            tool['description'] = description
            tool['code'] = code
            break
    else:  # for-else循环，如果循环正常结束（没有break），则执行
        tools.append({
            "name": name,
            "description": description,
            "code": code,
        })

    with open(TOOL_LIBRARY_FILE, 'w', encoding='utf-8') as f:
        json.dump(tools, f, indent=4, ensure_ascii=False)
    if log_func:
        log_func(f"工具 '{name}' 已成功保存。")
