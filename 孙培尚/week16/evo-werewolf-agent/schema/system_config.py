import os
from pydantic import BaseModel, Field, model_validator


class SystemConfig(BaseModel):
    base_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1", description="模型服务地址")
    api_key: str = Field(default="", description="模型认证API Key")
    default_model: str = Field(default="qwen-flash", description="默认模型名称")

    @model_validator(mode="after")
    def after_load_hook(self) -> "SystemConfig":
        # 环境变量优先
        env_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("DASHSCOPE_API_KEY")
        if env_key:
            self.api_key = env_key
        env_base_url = os.environ.get("OPENAI_BASE_URL")
        if env_base_url:
            self.base_url = env_base_url
        # 将 key 注入环境变量供 SDK 使用
        os.environ["OPENAI_API_KEY"] = self.api_key
        os.environ["OPENAI_BASE_URL"] = self.base_url
        return self


def load_system_config(file_path: str) -> SystemConfig:
    with open(file_path, "r", encoding="utf-8") as f:
        json_data = f.read()

    return SystemConfig.model_validate_json(json_data)
