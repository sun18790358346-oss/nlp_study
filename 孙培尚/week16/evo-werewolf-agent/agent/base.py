
from agents import Agent, Runner
from agents import set_default_openai_api, set_tracing_disabled
from schema.system_config import load_system_config

set_default_openai_api("chat_completions")
set_tracing_disabled(True)

config = load_system_config("config/system_config.json")


class BaseAgent:
    def __init__(self):
        self.agent = Agent(
            name="",
            model=config.default_model,
            instructions="你好",
        )

    async def run(self, input: str):
        result = await Runner.run(self.agent, input)
        return result.final_output
