# llm_interface.py
import openai
from config import LLM_API_KEY

# 设置API密钥
openai.api_key = LLM_API_KEY

def ask_llm(system_prompt, user_prompt):
    """
    与大语言模型进行单次交互的函数。
    - system_prompt: 定义AI角色的系统提示
    - user_prompt: 用户的具体请求
    返回LLM生成的文本响应。
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4-turbo-preview",  # 你可以换成任何你正在使用的模型
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3, # 较低的温度确保输出更稳定和可预测
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"与LLM API交互时出错: {e}")
        return None
