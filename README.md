# MCAA-Phase1 / 工匠学徒阶段一

This project is a proof of concept for building an AI assistant that can plan,
write and execute Python code. It demonstrates a simple workflow where the
system plans tasks using a large language model (LLM), generates Python scripts
for new tools, executes them and optionally stores successful tools for future
use.

**Warning**: the assistant executes generated code directly. Running this code
on your machine can be dangerous and may cause data loss or other issues. Use it
only for experimental purposes.

## Requirements
- Python 3.8+
- An LLM API key (e.g. OpenAI) placed in `config.py`

## Usage
1. Install dependencies (at least `openai`).
2. Put your API key in `config.py`.
3. Run the agent with `python main.py` and follow the prompts.

## 目录说明
- `main.py` 负责整体流程控制
- `config.py` 存放 LLM 的 API 密钥
- `llm_interface.py` 与大语言模型交互的封装
- `planner.py` 根据目标生成执行计划
- `coder.py` 根据计划中的需求生成 Python 脚本
- `executor.py` 执行生成的脚本并返回结果
- `memory_manager.py` 读写工具库 `tool_library.json`
- `generated_scripts/` 用于存放运行时生成的脚本

## 安全警告
本项目忽略了安全防护措施，直接执行 LLM 生成的代码，可能导致系统损坏或数据丢失。请勿在重要环境中运行，仅供学习和概念验证之用。
