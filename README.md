# MCAA-Phase1

## Overview 
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

## 介绍

### 1. 项目概述

MCAA-Phase1 是一个AI驱动的自动化任务执行代理。它通过集成大型语言模型（LLM），实现了从任务规划、Python代码生成与修改、代码执行到结果验证的完整工作流。项目支持命令行界面（CLI）和图形用户界面（GUI），并具备一定的错误处理和自我诊断能力。其核心目标是根据用户输入的目标，自动生成并执行相应的Python工具来完成任务。

### 2. 核心功能分析

项目由多个关键模块协同工作，完成从目标理解到任务执行的整个流程：

#### 2.1. 任务规划 (Planner - `planner.py`)

*   **功能**: Planner模块接收用户定义的任务目标和当前可用的工具列表。它通过LLM分析这些信息，选择合适的策略（直接使用现有工具、修改现有工具或创建新工具），并生成一个结构化的JSON计划。
*   **交互**: `Agent` 核心调用 `planner.create_plan()`，传入用户目标和LLM提供者。Planner内部会加载 `tool_library.json` 中的现有工具作为上下文信息提供给LLM。如果用户目标中包含验证相关的关键词，Planner会在计划中加入 `CREATE_VERIFICATION_TOOL` 步骤。

#### 2.2. 代码生成与修改 (Coder - `coder.py`)

*   **功能**: Coder模块负责根据LLM的指示生成新的Python脚本或修改现有脚本。它包含两个主要功能：`create_code()` 用于从头创建代码，`modify_code()` 用于基于现有代码和修改指令生成新代码。
*   **交互**: `Agent` 根据Planner生成的计划步骤，如果步骤类型是 `CREATE_NEW_TOOL` 或 `MODIFY_EXISTING_TOOL`，则调用Coder相应的方法。Coder使用特定的系统提示（`CODER_SYSTEM_PROMPT`, `MODIFIER_SYSTEM_PROMPT`）指导LLM生成纯Python代码。代码生成后会进行基本的清理（如移除Markdown标记）。

#### 2.3. 代码执行 (Executor - `executor.py`)

*   **功能**: Executor模块负责执行由Coder生成或从工具库加载的Python脚本，以及执行任意shell命令。它提供了 `run_script()` 和 `run_command()` 两个核心方法。
*   **交互**: `Agent` 在获得可执行代码后，调用 `executor.run_script()`。脚本会被保存到 `generated_scripts` 目录下并执行。`run_command()` 使用 `shlex` 安全地分割命令参数。两个方法都会捕获标准输出和标准错误，并返回执行成功与否的状态。

#### 2.4. 结果验证 (Verifier - `verifier.py`)

*   **功能**: Verifier模块用于生成一个验收测试脚本，以验证主任务是否成功执行。它根据原始用户目标和已执行代码的描述，通过LLM生成一个Python脚本。
*   **交互**: 如果计划中包含 `CREATE_VERIFICATION_TOOL` 步骤，`Agent` 会调用 `verifier.create_verification_code()`。生成的验证脚本随后也通过 `Executor` 执行。

#### 2.5. 错误处理与诊断 (ErrorHandler - `error_handler.py`, Diagnostician - `diagnostician.py`)

*   **ErrorHandler**:
    *   **功能**: `error_handler.analyze_error()` 在Agent执行过程中捕获到异常时被调用。它根据异常类型和内容，判断是否应该重试、重试延迟多久，并提供一个错误描述和指纹。
    *   **交互**: `Agent` 的 `_execute_with_retry()` 方法使用 `analyze_error()` 的结果来决定重试逻辑。
*   **Diagnostician**:
    *   **功能**: 当Agent遇到无法通过简单重试解决的致命错误时，`diagnostician.diagnose_and_plan()` 会被调用。它接收失败的上下文（目标、失败步骤、错误日志），通过LLM分析根本原因，并生成一个系统级修复计划。该计划可能包括运行命令、编写并执行修复脚本，或请求用户介入。
    *   **交互**: `Agent` 的主 `run()` 方法在捕获到顶层异常时调用诊断模块。如果诊断成功并生成了自我修复计划，`Agent` 会尝试执行该计划 (`_execute_repair_plan()`)，然后重试原始任务。

#### 2.6. 记忆与工具管理 (MemoryManager - `memory_manager.py`)

*   **功能**: `memory_manager` 负责持久化和检索可复用的Python工具。工具以JSON格式存储在 `tool_library.json` 文件中，包含工具名称、描述和代码。
*   **交互**: Planner在规划前通过 `load_tools()` 获取现有工具列表。Agent在成功执行创建或修改工具的步骤后，通过 `save_tool()` 将新工具或更新后的工具保存到库中，该函数会自动处理命名冲突。

#### 2.7. LLM 接口 (LLMInterface - `llm_interface.py`)

*   **功能**: `llm_interface` 封装了与不同大型语言模型服务（如OpenAI, Google）的交互逻辑。它定义了一个抽象基类 `LLMProvider` 和具体的实现类（如 `OpenAIProvider`, `GoogleProvider`）。API配置（密钥、模型列表、基础URL）存储在 `api_config.json` 中。
*   **交互**: 项目中所有需要与LLM通信的模块（Planner, Coder, Verifier, Diagnostician）都会接收一个 `LLMProvider` 实例，并通过其 `ask()` 方法发送请求。

#### 2.8. 用户界面 (GUI - `gui.py`, CLI - `main.py`)

*   **CLI (`main.py`)**:
    *   **功能**: 提供命令行入口。用户可以通过参数指定API提供者、模型、任务目标和是否启用验证模式。也支持交互式输入任务目标。
*   **GUI (`gui.py`)**:
    *   **功能**: 基于Tkinter的图形用户界面。用户可以管理API提供者配置，创建和管理多个任务。每个任务有独立的日志显示区域。支持任务的重新运行和迭代修改。
    *   **交互**: GUI通过 `Agent` 类执行任务，并通过队列机制异步更新日志和任务状态。`gui_provider_editor.py` 提供了API提供者配置的编辑对话框。


### 安装
1. 安装依赖：
```bash
pip install -r requirements.txt
```
2. 在 `api_config.json` 中配置 API 密钥和模型（当然也可以在GUI界面中配置）。

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

### 简要组件说明
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
