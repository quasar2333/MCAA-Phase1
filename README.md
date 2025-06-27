# MCAA-Phase1

A simple LLM powered agent that can run in either CLI or GUI mode.
Scripts generated during execution are stored under `generated_scripts/` and can optionally be saved as reusable tools.

## Setup

```bash
pip install -r requirements.txt
```

Edit `api_config.json` to add your API keys. The `base_url` field can usually be left empty for the OpenAI API unless you need a proxy or compatible service. Each provider entry lists the models that can be used.

## Running

### GUI
```bash
python gui.py
```
Select a provider from the list and create a new task to start an agent run.

### CLI
```bash
python main.py --provider openai_default --goal "create a folder named 'project_files'"
```
Omitting `--goal` starts an interactive loop.

## Warning
The agent executes generated Python code directly which may be unsafe. Review any generated scripts before running them in a production environment.
