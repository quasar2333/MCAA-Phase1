# config.py
# 在这里配置默认的模型提供商名称，可通过环境变量 OVERRIDE_PROVIDER 覆盖
import os
DEFAULT_PROVIDER = os.getenv("OVERRIDE_PROVIDER", "default")
# 默认模型ID，如未指定则使用提供商配置中的第一个模型，可通过 OVERRIDE_MODEL 覆盖
DEFAULT_MODEL = os.getenv("OVERRIDE_MODEL", "")

# API供应商配置存放的文件
API_CONFIG_FILE = "api_config.json"
