"""
llm_demo — LLM 智能缓存 SDK (生产级封装)

基于 redis-vl 封装，提供统一的生产级 LLM 缓存组件：

    from llm_demo import SemanticCache

    cache = SemanticCache(name="llmcache", redis_url="redis://localhost:6379")
    cache.store(prompt="法国的首都是什么？", response="巴黎")
    result = cache.check(prompt="法国首都")

组件列表:
    - SemanticCache:           LLM 语义缓存（提问→回答）
    - EmbeddingsCache:         Embedding 向量缓存
    - SemanticMessageHistory:  对话历史管理
    - SemanticRouter:          语义意图路由
    - Route:                   路由定义

安装:
    pip install redisvl
    # 如需本地向量化:
    pip install sentence-transformers
"""

__version__ = "1.0.0"

from .work01_SemanticCache import SemanticCache
from .work01_EmbeddingsCache import EmbeddingsCache
from .work01_SemanticMessageHistory import SemanticMessageHistory
from .work01_SemanticRouter import SemanticRouter, Route

__all__ = [
    "SemanticCache",
    "EmbeddingsCache",
    "SemanticMessageHistory",
    "SemanticRouter",
    "Route",
]
