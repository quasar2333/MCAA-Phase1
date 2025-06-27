import json
from typing import List, Dict, Any

from config import API_CONFIG_FILE


def load_providers() -> List[Dict[str, Any]]:
    """Load all provider configurations."""
    try:
        with open(API_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_providers(providers: List[Dict[str, Any]]):
    with open(API_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(providers, f, indent=4, ensure_ascii=False)


def add_or_update_provider(name: str, provider_type: str, base_url: str, api_key: str, models: List[str]):
    """Add a provider or update existing one."""
    providers = load_providers()
    for p in providers:
        if p['name'] == name:
            p['type'] = provider_type
            p['base_url'] = base_url
            p['api_key'] = api_key
            p['models'] = models
            break
    else:
        providers.append({
            'name': name,
            'type': provider_type,
            'base_url': base_url,
            'api_key': api_key,
            'models': models,
        })
    save_providers(providers)


def delete_provider(name: str):
    providers = load_providers()
    providers = [p for p in providers if p['name'] != name]
    save_providers(providers)


def get_provider(name: str) -> Dict[str, Any] | None:
    for p in load_providers():
        if p['name'] == name:
            return p
    return None
