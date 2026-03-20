from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing_extensions import Literal
import openai
import json

# 初始化
app = FastAPI(title="翻译智能体API")
client = openai.OpenAI(
    api_key="sk-abuf970c557d41b9899269dc981366f9",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


# ============= 输入模型 =============
class TranslateRequest(BaseModel):
    """翻译请求"""
    query: str = Field(..., description="用户的翻译请求，如：'帮我将good！翻译为中文'")


# ============= 输出模型 =============
class TranslationInfo(BaseModel):
    """提取的翻译信息"""
    source_language: Literal["auto", "中文", "英文", "日文", "韩文"] = Field(
        default="auto",
        description="原始语种"
    )
    target_language: Literal["中文", "英文", "日文", "韩文"] = Field(
        ...,
        description="目标语种"
    )
    text_to_translate: str = Field(
        ...,
        description="待翻译的文本"
    )


# ============= 翻译智能体 =============
class TranslationAgent:
    def __init__(self, model: str = "qwen3.5-plus"):
        self.model = model

    def extract(self, query: str) -> TranslationInfo:
        """从查询中提取翻译信息"""
        tools = [{
            "type": "function",
            "function": {
                "name": "extract_translation",
                "description": "提取翻译信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "source_language": {
                            "type": "string",
                            "enum": ["auto", "中文", "英文", "日文", "韩文"],
                            "description": "原始语种"
                        },
                        "target_language": {
                            "type": "string",
                            "enum": ["中文", "英文", "日文", "韩文"],
                            "description": "目标语种"
                        },
                        "text_to_translate": {
                            "type": "string",
                            "description": "待翻译文本"
                        }
                    },
                    "required": ["target_language", "text_to_translate"]
                }
            }
        }]

        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": query}],
            tools=tools,
            tool_choice="auto"
        )

        try:
            args = response.choices[0].message.tool_calls[0].function.arguments
            return TranslationInfo(**json.loads(args))
        except:
            raise HTTPException(status_code=400, detail="无法提取翻译信息")


agent = TranslationAgent()


@app.post("/transaction", response_model=TranslationInfo)
async def translate(request: TranslateRequest):
    """
    从翻译请求中提取原始语种、目标语种和待翻译文本

    示例：
    输入：{"query": "帮我将good！翻译为中文"}
    输出：{
        "source_language": "英文",
        "target_language": "中文",
        "text_to_translate": "good！"
    }
    """
    return agent.extract(request.query)
