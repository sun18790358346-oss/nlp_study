"""
EmbeddingsCache — 嵌入向量缓存组件

基于 redis-vl 的 EmbeddingsCache，用于缓存文本到向量的转换结果。
避免对相同内容重复调用 embedding 模型，节约计算资源和时间。

用法示例:
    from llm_cache import EmbeddingsCache

    cache = EmbeddingsCache(
        name="embed_cache",
        redis_url="redis://localhost:6379",
        ttl=3600
    )

    # 存储
    key = cache.set(content="机器学习是什么？", model_name="all-MiniLM-L6-v2", embedding=[...])

    # 查询
    result = cache.get(content="机器学习是什么？", model_name="all-MiniLM-L6-v2")
    if result:
        print(result["embedding"])
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Optional, Union

from redisvl.extensions.cache.embeddings import EmbeddingsCache as _RedisVLEmbeddingsCache

logger = logging.getLogger(__name__)


class EmbeddingsCache:
    """嵌入向量缓存

    将文本的 embedding 向量缓存到 Redis，避免对相同文本重复计算 embedding。
    使用 MD5 哈希（由 redis-vl 内部处理）作为 key，确保精确匹配。

    Args:
        name: 缓存名称
        redis_url: Redis 连接 URL
        ttl: 缓存过期时间（秒），None 永不过期
        connection_kwargs: Redis 连接附加参数
    """

    def __init__(
        self,
        name: str = "embed_cache",
        redis_url: str = "redis://localhost:6379",
        ttl: Optional[int] = None,
        connection_kwargs: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.ttl = ttl

        try:
            self._cache = _RedisVLEmbeddingsCache(
                name=name,
                redis_url=redis_url,
                ttl=ttl,
                connection_kwargs=connection_kwargs or {},
            )
            logger.info("EmbeddingsCache '%s' initialized (ttl=%s)", name, ttl)
        except Exception as e:
            logger.error("Failed to initialize EmbeddingsCache '%s': %s", name, e)
            raise

    # ---- 单条操作 ----

    def set(
        self,
        content: Union[str, bytes],
        model_name: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None,
    ) -> str:
        """存储一条文本的 embedding 向量

        Args:
            content: 原始文本
            model_name: embedding 模型名称
            embedding: 向量值（float 列表）
            metadata: 附加元数据
            ttl: 本条过期时间（秒）

        Returns:
            缓存 key
        """
        try:
            key = self._cache.set(
                content=content,
                model_name=model_name,
                embedding=embedding,
                metadata=metadata,
                ttl=ttl,
            )
            logger.debug("Stored embedding key=%s", key)
            return key
        except Exception as e:
            logger.error("Failed to store embedding: %s", e)
            raise RuntimeError(f"Failed to store embedding: {e}") from e

    def get(
        self, content: Union[str, bytes], model_name: str
    ) -> Optional[Dict[str, Any]]:
        """查询文本的 embedding 缓存

        Args:
            content: 原始文本
            model_name: embedding 模型名称

        Returns:
            缓存记录（含 embedding、content、model_name 等字段），未命中返回 None
        """
        try:
            result = self._cache.get(content=content, model_name=model_name)
            return result
        except Exception as e:
            logger.error("Failed to get embedding: %s", e)
            return None

    def exists(self, content: Union[str, bytes], model_name: str) -> bool:
        """检查是否存在该文本的 embedding 缓存

        Args:
            content: 原始文本
            model_name: embedding 模型名称

        Returns:
            是否存在
        """
        try:
            return self._cache.exists(content=content, model_name=model_name)
        except Exception as e:
            logger.error("Failed to check embedding exists: %s", e)
            return False

    def drop(self, content: Union[str, bytes], model_name: str) -> None:
        """删除指定文本的 embedding 缓存

        Args:
            content: 原始文本
            model_name: embedding 模型名称
        """
        try:
            self._cache.drop(content=content, model_name=model_name)
            logger.debug("Dropped embedding for content='%s' model='%s'", content, model_name)
        except Exception as e:
            logger.error("Failed to drop embedding: %s", e)

    # ---- 批量操作 ----

    def mset(
        self, items: List[Dict[str, Any]], ttl: Optional[int] = None
    ) -> List[str]:
        """批量存储 embedding

        Args:
            items: 记录列表，每条须含 content、model_name、embedding 字段
            ttl: 过期时间

        Returns:
            key 列表
        """
        try:
            return self._cache.mset(items=items, ttl=ttl)
        except Exception as e:
            logger.error("Failed to batch store embeddings: %s", e)
            raise RuntimeError(f"Failed to batch store embeddings: {e}") from e

    def mget(
        self, contents: Iterable[Union[str, bytes]], model_name: str
    ) -> List[Optional[Dict[str, Any]]]:
        """批量查询 embedding

        Args:
            contents: 文本列表
            model_name: 模型名称

        Returns:
            结果列表（与输入顺序对应）
        """
        try:
            return self._cache.mget(contents=contents, model_name=model_name)
        except Exception as e:
            logger.error("Failed to batch get embeddings: %s", e)
            return []

    def mexists(
        self, contents: Iterable[Union[str, bytes]], model_name: str
    ) -> List[bool]:
        """批量检查是否存在

        Args:
            contents: 文本列表
            model_name: 模型名称

        Returns:
            是否存在列表
        """
        try:
            return self._cache.mexists(contents=contents, model_name=model_name)
        except Exception as e:
            logger.error("Failed to batch check embeddings: %s", e)
            return [False] * len(list(contents))

    # ---- 维护 ----

    def clear(self) -> None:
        """清空所有 embedding 缓存"""
        try:
            self._cache.clear()
            logger.info("EmbeddingsCache '%s' cleared", self.name)
        except Exception as e:
            logger.error("Failed to clear embeddings cache: %s", e)
            raise RuntimeError(f"Failed to clear embeddings cache: {e}") from e

    def set_ttl(self, ttl: Optional[int] = None) -> None:
        """动态调整过期时间

        Args:
            ttl: 过期秒数，None 永不过期
        """
        self.ttl = ttl
        self._cache.set_ttl(ttl)
        logger.info("EmbeddingsCache TTL updated to %s", ttl)

    def disconnect(self) -> None:
        """断开 Redis 连接"""
        try:
            self._cache.disconnect()
        except Exception as e:
            logger.warning("Disconnect error: %s", e)

    # ---- 兼容旧接口 ----

    def store(self, text: Union[str, List[str]], embedding: Any) -> Any:
        """兼容旧项目接口：存储 embedding

        注意：旧接口只传 text 和 embedding，不包含 model_name。
        这里自动使用默认模型名 "legacy"。
        """
        if isinstance(text, str):
            text = [text]

        embeddings = embedding if hasattr(embedding, "__iter__") else [embedding]

        try:
            with self._cache._redis.pipeline() as pipe:
                for t, emb in zip(text, embeddings):
                    # 使用底层 Redis 直接操作（保持旧接口兼容性）
                    import hashlib
                    import numpy as np

                    t_code = hashlib.md5(t.encode()).hexdigest()
                    key = f"{self.name}:{t_code}"
                    value = np.array(emb).tobytes() if not isinstance(emb, bytes) else emb
                    pipe.setex(key, self.ttl or 86400, value)
                return pipe.execute()
        except Exception as e:
            logger.error("Legacy store failed: %s", e)
            return -1

    def call(self, text: Union[str, List[str]]) -> Optional[List]:
        """兼容旧项目接口：查询 embedding

        返回 numpy 数组或 None
        """
        import numpy as np

        if isinstance(text, str):
            text = [text]

        try:
            import hashlib

            keys = [f"{self.name}:{hashlib.md5(t.encode()).hexdigest()}" for t in text]
            results = self._cache._redis.mget(keys)

            if not results or all(r is None for r in results):
                return None

            embeddings = []
            for r in results:
                if r is None:
                    embeddings.append(None)
                else:
                    embeddings.append(np.frombuffer(r, dtype=np.float32))
            return embeddings
        except Exception as e:
            logger.error("Legacy call failed: %s", e)
            return None

    def delete(self, text: Union[str, List[str]]) -> Any:
        """兼容旧项目接口：删除 embedding"""
        import hashlib

        if isinstance(text, str):
            text = [text]

        try:
            keys = [f"{self.name}:{hashlib.md5(t.encode()).hexdigest()}" for t in text]
            return self._cache._redis.delete(*keys)
        except Exception as e:
            logger.error("Legacy delete failed: %s", e)
            return -1

    def __repr__(self) -> str:
        return f"EmbeddingsCache(name='{self.name}', ttl={self.ttl})"
