# llm_interface.py
import json
import os # Import os module to access environment variables
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import openai
import google.generativeai as genai
from dotenv import load_dotenv

from settings import API_CONFIG_FILE

# Load .env file at the module level so environment variables are available early
load_dotenv()

class LLMProvider(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # Prioritize environment variables, then config file, then default to empty
        # Specific providers will handle their specific env var names
        self.api_key = config.get('api_key', '') # Placeholder, actual loading in subclasses
        self.models = config.get('models', [])
        self.selected_model = self.models[0] if self.models else None
        self._load_api_key() # Call method to load API key correctly

    @abstractmethod
    def _load_api_key(self):
        """Loads API key, prioritizing environment variables."""
        pass

    @abstractmethod
    def ask(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
        pass

    def get_name(self) -> str:
        return self.config.get('name', 'Unknown')

    def get_available_models(self) -> List[str]:
        return self.models

class OpenAIProvider(LLMProvider):
    def _load_api_key(self):
        env_key = os.getenv('OPENAI_API_KEY')
        if env_key:
            self.api_key = env_key
        else:
            self.api_key = self.config.get('api_key', '')

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config) # This will call _load_api_key()
        self.client = openai.OpenAI(
            api_key=self.api_key, # API key is now loaded by _load_api_key
            base_url=config.get('base_url') or None,
        )

    def ask(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
        if not self.api_key or self.api_key.startswith('sk-YOUR'): # Check for placeholder
            raise ValueError(f"提供者 '{self.get_name()}' 的 OpenAI API 密钥未配置 (环境变量 OPENAI_API_KEY 或配置文件)。")
        
        target_model = model or self.selected_model
        if not target_model:
            raise ValueError(f"提供者 '{self.get_name()}' 没有可用模型或未选择模型。")
            
        response = self.client.chat.completions.create(
            model=target_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

class GoogleProvider(LLMProvider):
    def _load_api_key(self):
        env_key = os.getenv('GOOGLE_API_KEY')
        if env_key:
            self.api_key = env_key
        else:
            self.api_key = self.config.get('api_key', '')

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config) # This will call _load_api_key()
        if self.api_key and not self.api_key.startswith('YOUR_GOOGLE'): # Check for placeholder
            genai.configure(api_key=self.api_key) # API key is now loaded

    def ask(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
        if not self.api_key or self.api_key.startswith('YOUR_GOOGLE'): # Check for placeholder
            raise ValueError(f"提供者 '{self.get_name()}' 的 Google API 密钥未配置 (环境变量 GOOGLE_API_KEY 或配置文件)。")

        target_model = model or self.selected_model
        if not target_model:
            raise ValueError(f"提供者 '{self.get_name()}' 没有可用模型或未选择模型。")
            
        model_instance = genai.GenerativeModel(
            model_name=target_model,
            system_instruction=system_prompt
        )
        response = model_instance.generate_content(user_prompt)
        return response.text.strip()


PROVIDER_CLASSES = {
    "openai": OpenAIProvider,
    "google": GoogleProvider,
}

def get_provider(provider_name: str) -> Optional[LLMProvider]:
    # load_dotenv() is already called at module level
    try:
        with open(API_CONFIG_FILE, 'r', encoding='utf-8') as f:
            configs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        configs = [] # Proceed with empty configs, rely on env vars or default provider behavior

    provider_config = None
    for cfg in configs:
        if cfg['name'] == provider_name:
            provider_config = cfg
            break

    # If provider_name not in config, create a default config for it
    # This allows using providers purely from env vars if not in api_config.json
    if not provider_config:
        # Try to guess type based on common naming, or default to openai
        # This part might need refinement if more provider types are added
        # For now, it assumes if not found, we might be trying to init with env vars only
        provider_type_guess = 'google' if 'google' in provider_name.lower() else 'openai'
        provider_config = {"name": provider_name, "type": provider_type_guess, "models": []}


    provider_type = provider_config.get('type')
    if provider_type in PROVIDER_CLASSES:
        try:
            return PROVIDER_CLASSES[provider_type](provider_config)
        except Exception as e:
            # Use a simple print for this error as it's at provider init time
            print(f"初始化提供者 {provider_name} 失败: {e}")
            return None
    else:
        print(f"未知提供者类型 '{provider_type}' for '{provider_name}'.")
        return None


def load_provider_configs() -> List[Dict[str, Any]]:
    try:
        with open(API_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_provider_configs(configs: List[Dict[str, Any]]):
    with open(API_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(configs, f, indent=4, ensure_ascii=False)