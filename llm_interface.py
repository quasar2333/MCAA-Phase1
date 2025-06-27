# llm_interface.py
"""Interface to different LLM providers."""
from config import DEFAULT_PROVIDER, DEFAULT_MODEL
from api_manager import get_provider


def _ask_openai(base_url: str, model_id: str, api_key: str, system_prompt: str, user_prompt: str):
    import openai
    openai.api_key = api_key
    if base_url:
        openai.base_url = base_url
    response = openai.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def _ask_google(model_id: str, api_key: str, system_prompt: str, user_prompt: str):
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_id)
    # google generative models only accept 'user' and 'model' roles. Use
    # `system_instruction` to provide the system prompt.
    response = model.generate_content(
        [user_prompt],
        system_instruction=system_prompt
    )
    return response.text.strip()

def ask_llm(system_prompt: str, user_prompt: str, provider_name: str = DEFAULT_PROVIDER, model_id: str | None = None):
    """与指定的LLM提供商进行单次交互。"""
    provider = get_provider(provider_name)
    if not provider:
        print(f"未找到名称为 '{provider_name}' 的提供商配置")
        return None

    try:
        model_id = model_id or (provider.get('models') or [DEFAULT_MODEL])[0]
        if provider['type'] == 'openai':
            return _ask_openai(provider.get('base_url', ''), model_id, provider['api_key'], system_prompt, user_prompt)
        elif provider['type'] == 'google':
            return _ask_google(model_id, provider['api_key'], system_prompt, user_prompt)
        else:
            print(f"未知的提供商类型: {provider['type']}")
            return None
    except Exception as e:
        print(f"与LLM API交互时出错: {e}")
        return None
