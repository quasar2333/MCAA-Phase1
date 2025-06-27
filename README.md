# MCAA-Phase1 / 工匠学徒阶段一

This project is a proof of concept for building an AI assistant that can plan, write and execute Python code. It demonstrates a simple workflow where the system plans tasks using a large language model (LLM), generates Python scripts for new tools, executes them and optionally stores successful tools for future use. A simple Tkinter GUI lets you manage API providers, create tasks and watch their logs.

本项目展示了一个 AI 助手的基础工作流：从任务规划、代码生成到执行，并可选地保存成功的工具。提供了简易的 Tkinter 图形界面，可管理多个 API 供应商、创建并监控任务。

**Warning**: the assistant executes generated code directly. Running this code on your machine can be dangerous and may cause data loss or other issues. Use it only for experimental purposes.

**警告**：本项目会直接执行生成的代码，存在潜在风险，仅供学习和实验，请勿在重要环境中运行。

## Requirements
- Python 3.8+
- Python packages: at least `openai`. `google-generativeai` is required for Google models.
- LLM provider settings stored in `api_config.json` (editable via `gui.py`). Each provider can define multiple model IDs.

## Usage / 使用方法
1. Install dependencies (at least `openai`).
2. Edit or create providers in `api_config.json` or run `python gui.py` for a graphical interface. **Be sure to replace the placeholder API key** with your real key. Each provider may contain multiple model IDs.
3. Run the agent with `python main.py --provider PROVIDER_NAME --model MODEL_ID` or start the GUI with `python gui.py`. In the GUI you can create several tasks, start them and monitor their logs.
4. You can override the default provider and model via the environment variables `OVERRIDE_PROVIDER` and `OVERRIDE_MODEL` before running `main.py` or `gui.py`.

1. 安装依赖（至少需要 `openai`）。
2. 编辑 `api_config.json` 或运行 `python gui.py` 以图形界面管理供应商。**请务必将占位符 API key 替换为真实 key**，每个供应商可包含多个模型 ID。
3. 通过 `python main.py --provider PROVIDER_NAME --model MODEL_ID` 启动命令行，或运行 `python gui.py` 使用图形界面。在 GUI 中可以创建多个任务、启动并查看日志。
4. 运行前可设置环境变量 `OVERRIDE_PROVIDER` 和 `OVERRIDE_MODEL` 覆盖默认供应商和模型。

## 目录说明
- `main.py` 负责整体流程控制
- `config.py` 定义默认提供商和配置文件路径
- `llm_interface.py` 与大语言模型交互的封装
- `planner.py` 根据目标生成执行计划
- `coder.py` 根据计划中的需求生成 Python 脚本
- `executor.py` 执行生成的脚本并返回结果
- `memory_manager.py` 读写工具库 `tool_library.json`
- `generated_scripts/` 用于存放运行时生成的脚本

## 安全警告
本项目忽略了安全防护措施，直接执行 LLM 生成的代码，可能导致系统损坏或数据丢失。请勿在重要环境中运行，仅供学习和概念验证之用。
