# gpt_llm_api.py
import openai
import json
import uvicorn
from fastapi import FastAPI, Query

# 读取提示词文件
with open('prompt.md', 'r', encoding='utf-8') as f:
    SYSTEM_PROMPT = f.read()


client = openai.OpenAI(
    api_key="sk-1f8f970c557d41xxxxxc981366f9",  # 账号绑定的

    # 大模型厂商的地址
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

app = FastAPI()


@app.get("/parse")
async def parse(text: str = Query(..., description="要解析的文本")):
    try:
        response = client.chat.completions.create(
            model="qwen-plus",  # 使用 GPT-3.5-turbo 模型
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},  # 系统提示词
                {"role": "user", "content": text}  # 用户输入
            ],
            temperature=0.1,  # 低温度保证稳定性
            max_tokens=500  # 限制返回长度
        )

        # 返回模型生成的文本
        content = response.choices[0].message.content

        result = json.loads(content)
        # 3. 返回JSON对象（FastAPI自动转成JSON响应）
        return result

    except Exception as e:
        return f"解析失败: {str(e)}"
