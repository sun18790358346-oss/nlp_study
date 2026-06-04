"""
SemanticCache — LLM 语义缓存组件

基于 redis-vl 的 SemanticCache，用于缓存 LLM 的请求-回答对。
通过语义相似度匹配，语义相近的问题可直接返回缓存结果，
避免重复调用 LLM，降低延迟和成本。

用法示例:
    from llm_cache import SemanticCache
    from redisvl.utils.vectorize import HFTextVectorizer

    cache = SemanticCache(
        name="llmcache",
        redis_url="redis://localhost:6379",
        distance_threshold=0.1
    )

    # 存储
    cache.store(prompt="法国的首都是什么？", response="巴黎")

    # 语义匹配查询
    results = cache.check(prompt="法国首都")
    if results:
        print(results[0]["response"])  # "巴黎"
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import redis
from redisvl.extensions.cache.llm import SemanticCache as _RedisVLSemanticCache
from redisvl.utils.vectorize import BaseVectorizer

logger = logging.getLogger(__name__)


class SemanticCache:
    """LLM 语义缓存

    基于语义相似度匹配的 LLM 请求-回答缓存组件。
    底层使用 redis-vl 的 SemanticCache，利用 Redis 向量搜索
    实现高效的语义匹配。

    Args:
        name: 缓存名称（在 Redis 中用作 key 前缀）
        redis_url: Redis 连接 URL，如 "redis://localhost:6379"
        distance_threshold: 语义距离阈值，[0, 1]，越小匹配越严格
        ttl: 缓存过期时间（秒），None 表示永不过期
        vectorizer: 向量化器实例。不传时要求 check/store 时外部提供向量
        redis_password: Redis 密码（兼容旧接口，建议用 redis_url 传入）
        connection_kwargs: Redis 连接附加参数
        overwrite: 同名缓存是否重建索引
    """

    def __init__(
        self,
        name: str = "llmcache",
        redis_url: str = "redis://localhost:6379",
        distance_threshold: float = 0.1,
        ttl: Optional[int] = None,
        vectorizer: Optional[BaseVectorizer] = None,
        redis_password: Optional[str] = None,
        connection_kwargs: Optional[Dict[str, Any]] = None,
        overwrite: bool = False,
    ):
        self.name = name
        self.distance_threshold = distance_threshold
        self.ttl = ttl

        # 兼容旧接口的 redis_password 参数
        _connection_kwargs = connection_kwargs or {}
        if redis_password:
            _connection_kwargs.setdefault("password", redis_password)

        try:
            self._cache = _RedisVLSemanticCache(
                name=name,
                redis_url=redis_url,
                distance_threshold=distance_threshold,
                ttl=ttl,
                vectorizer=vectorizer,
                connection_kwargs=_connection_kwargs,
                overwrite=overwrite,
            )
            logger.info("SemanticCache '%s' initialized (threshold=%.2f, ttl=%s)", name, distance_threshold, ttl)
        except Exception as e:
            logger.error("Failed to initialize SemanticCache '%s': %s", name, e)
            raise

    # ---- 核心 API ----

    def store(
        self,
        prompt: str,
        response: str,
        vector: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None,
    ) -> str:
        """存储一条 LLM 请求-回答对到缓存

        Args:
            prompt: 用户提问文本
            response: LLM 回答文本
            vector: 提问的向量表示（不传则用 vectorizer 自动计算）
            metadata: 附加元数据（如 model="gpt-4", temperature=0.7）
            filters: 过滤条件（用于分字段过滤）
            ttl: 本条缓存的过期时间（秒），覆盖全局 ttl

        Returns:
            缓存记录的 key

        Raises:
            RuntimeError: 存储失败时
        """
        try:
            key = self._cache.store(
                prompt=prompt,
                response=response,
                vector=vector,
                metadata=metadata,
                filters=filters,
                ttl=ttl,
            )
            logger.debug("Stored cache key=%s prompt='%s'", key, prompt[:50])
            return key
        except Exception as e:
            logger.error("Failed to store cache: %s", e)
            raise RuntimeError(f"Failed to store cache: {e}") from e

    def check(
        self,
        prompt: Optional[str] = None,
        vector: Optional[List[float]] = None,
        num_results: int = 1,
        return_fields: Optional[List[str]] = None,
        distance_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """检查缓存中是否有语义相似的提问

        如果缓存命中，返回结果列表（按距离升序排列）；
        未命中返回空列表。

        Args:
            prompt: 提问文本（与 vector 二选一）
            vector: 提问的向量（与 prompt 二选一）
            num_results: 最多返回的结果数
            return_fields: 返回的字段列表，默认返回全部字段
            distance_threshold: 临时覆盖全局阈值

        Returns:
            匹配的缓存记录列表，每条包含 response、prompt、distance 等字段
            未命中时返回空列表 []
        """
        try:
            results = self._cache.check(
                prompt=prompt,
                vector=vector,
                num_results=num_results,
                return_fields=return_fields,
                distance_threshold=distance_threshold,
            )
            return results or []
        except Exception as e:
            logger.error("Failed to check cache: %s", e)
            return []

    def clear(self) -> None:
        """清空当前缓存的所有数据"""
        try:
            self._cache.clear()
            logger.info("Cache '%s' cleared", self.name)
        except Exception as e:
            logger.error("Failed to clear cache '%s': %s", self.name, e)
            raise RuntimeError(f"Failed to clear cache: {e}") from e

    def delete(self) -> None:
        """删除缓存索引和数据"""
        try:
            self._cache.delete()
            logger.info("Cache '%s' deleted", self.name)
        except Exception as e:
            logger.error("Failed to delete cache '%s': %s", self.name, e)
            raise RuntimeError(f"Failed to delete cache: {e}") from e

    def drop(self, ids: Optional[List[str]] = None, keys: Optional[List[str]] = None) -> None:
        """按 ID 或 key 删除特定缓存记录

        Args:
            ids: Redis 内部 ID 列表
            keys: 缓存 key 列表
        """
        try:
            self._cache.drop(ids=ids, keys=keys)
        except Exception as e:
            logger.error("Failed to drop from cache: %s", e)
            raise RuntimeError(f"Failed to drop from cache: {e}") from e

    def set_threshold(self, distance_threshold: float) -> None:
        """动态调整语义距离阈值

        Args:
            distance_threshold: 新的阈值 [0, 1]
        """
        self.distance_threshold = distance_threshold
        self._cache.set_threshold(distance_threshold)
        logger.info("Threshold updated to %.2f", distance_threshold)

    def set_ttl(self, ttl: Optional[int] = None) -> None:
        """动态调整缓存过期时间

        Args:
            ttl: 过期秒数，None 表示永不过期
        """
        self.ttl = ttl
        self._cache.set_ttl(ttl)
        logger.info("TTL updated to %s", ttl)

    def expire(self, key: str, ttl: Optional[int] = None) -> None:
        """设置特定 key 的过期时间

        Args:
            key: 缓存 key
            ttl: 过期秒数，None 使用全局 ttl
        """
        self._cache.expire(key, ttl=ttl)

    def disconnect(self) -> None:
        """断开 Redis 连接"""
        try:
            self._cache.disconnect()
        except Exception as e:
            logger.warning("Disconnect error: %s", e)

    # ---- 兼容旧接口 ----

    def call(self, prompt: str) -> Optional[str]:
        """兼容旧项目接口：查询缓存并直接返回第一个回答

        Args:
            prompt: 提问文本

        Returns:
            缓存的回答文本，未命中返回 None
        """
        results = self.check(prompt=prompt, num_results=1)
        if results:
            return results[0].get("response")
        return None

    def clear_cache(self) -> None:
        """兼容旧项目接口：清空缓存"""
        self.clear()

    def __repr__(self) -> str:
        return (
            f"SemanticCache(name='{self.name}', "
            f"threshold={self.distance_threshold}, "
            f"ttl={self.ttl})"
        )
