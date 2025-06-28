# MCAA-Phase1

## Overview (English)
MCAA-Phase1 is a refactored AI agent that can operate through a command line interface or a graphical user interface. It orchestrates large language model calls to plan, generate, execute and verify Python tools.

### Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. Configure API keys and models in `api_config.json`.

### CLI Usage
```bash
python main.py --provider <provider_name> --goal "your task" [--verify]
```
* `--provider` selects an entry from `api_config.json`.
* `--goal` is the task description.
* `--verify` enables creation of a verification step.

### GUI Usage
Simply run:
```bash
python gui.py
```
Use the interface to manage providers and tasks.

### Modules
- **agent_core.Agent** – central class controlling planning, coding, execution and optional verification. Handles retries and diagnostics.
- **planner** – uses an LLM to produce a JSON task plan.
- **coder** – creates or modifies Python tools according to prompts.
- **executor** – runs shell commands or generated scripts safely.
- **verifier** – builds verification scripts for completed tasks.
- **diagnostician** – analyzes fatal errors and suggests repair steps.
- **memory_manager** – stores and retrieves reusable tools.
- **error_handler** – suggests retry strategies when exceptions occur.
- **llm_interface** – abstracts different LLM providers such as OpenAI or Google.
- **gui.App** – tkinter based application for managing multiple tasks visually.
- **gui_provider_editor.ProviderEditor** – dialog for editing provider settings.
- **main** – entry point for CLI mode.
- **settings** – defines file locations for configurations and generated scripts.

## 中文介绍
MCAA‑Phase1 是一个经过重构的 AI Agent，既可以在命令行中运行，也提供图形界面。它通过调用大型语言模型来规划、生成、执行并验证 Python 工具。

### 安装
1. 安装依赖：
```bash
pip install -r requirements.txt
```
2. 在 `api_config.json` 中配置 API 密钥和模型。

### 命令行使用
```bash
python main.py --provider <provider_name> --goal "任务描述" [--verify]
```
* `--provider` 指定 `api_config.json` 中的提供者名称。
* `--goal` 为任务目标。
* `--verify` 开启自我验证步骤。

### 图形界面使用
运行：
```bash
python gui.py
```
在界面中管理 API 提供者和任务。

### 组件说明
- **agent_core.Agent** – 核心类，负责规划、生成代码、执行以及可选的验证，并在失败时进行诊断和重试。
- **planner** – 使用 LLM 生成 JSON 格式的任务计划。
- **coder** – 根据描述创建或修改 Python 工具。
- **executor** – 安全地执行命令或脚本。
- **verifier** – 为完成的任务生成验收脚本。
- **diagnostician** – 当任务出现致命错误时给出修复方案。
- **memory_manager** – 保存和读取可复用的工具代码。
- **error_handler** – 解析异常并给出是否重试的策略。
- **llm_interface** – 封装 OpenAI、Google 等 LLM 服务。
- **gui.App** – 基于 tkinter 的多任务图形界面。
- **gui_provider_editor.ProviderEditor** – 用于编辑 API 提供者的对话框。
- **main** – 命令行模式入口。
- **settings** – 配置文件及生成脚本的路径设置。
