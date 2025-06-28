# llm_interface.py
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import openai
import google.generativeai as genai

from settings import API_CONFIG_FILE

class LLMProvider(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key', '')
        self.models = config.get('models', [])
        self.selected_model = self.models[0] if self.models else None

    @abstractmethod
    def ask(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
        pass

    def get_name(self) -> str:
        return self.config.get('name', 'Unknown')

class OpenAIProvider(LLMProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=config.get('base_url') or None,
        )

    def ask(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
        if not self.api_key or self.api_key.startswith('sk-YOUR'):
            raise ValueError(f"提供者 '{self.get_name()}' 的 API 密钥未配置。")
        
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
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if self.api_key and not self.api_key.startswith('YOUR_GOOGLE'):
            genai.configure(api_key=self.api_key)

    def ask(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
        if not self.api_key or self.api_key.startswith('YOUR_GOOGLE'):
            raise ValueError(f"提供者 '{self.get_name()}' 的 API 密钥未配置。")

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
    try:
        with open(API_CONFIG_FILE, 'r', encoding='utf-8') as f:
            configs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

    for config in configs:
        if config['name'] == provider_name:
            provider_type = config.get('type', 'openai')
            if provider_type in PROVIDER_CLASSES:
                try:
                    return PROVIDER_CLASSES[provider_type](config)
                except Exception as e:
                    print(f"初始化提供者 {provider_name} 失败: {e}")
                    return None
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