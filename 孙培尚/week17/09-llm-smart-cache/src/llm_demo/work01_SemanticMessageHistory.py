"""
SemanticMessageHistory — 语义对话历史管理组件

基于 redis-vl 的 SemanticMessageHistory，用于存储和检索 LLM 对话历史。
支持按角色过滤、语义检索和窗口截取。

用法示例:
    from llm_cache import SemanticMessageHistory

    history = SemanticMessageHistory(
        name="my-session",
        redis_url="redis://localhost:6379",
    )

    # 添加消息
    history.add_messages([
        {"role": "user", "content": "hello"},
        {"role": "llm", "content": "hi there", "metadata": {"model": "gpt-4"}},
    ])

    # 获取最近消息
    recent = history.get_recent(top_k=5)

    # 语义检索
    relevant = history.get_relevant("weather", top_k=3)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

from redisvl.extensions.message_history import (
    SemanticMessageHistory as _RedisVLSemanticMessageHistory,
)

logger = logging.getLogger(__name__)


class SemanticMessageHistory:
    """语义对话历史管理

    基于 Redis 向量搜索的对话历史存储，支持：
    - 按 session 隔离存储
    - 按角色过滤
    - 语义检索历史
    - 时间窗口截取

    Args:
        name: 会话名称（类似 session id）
        redis_url: Redis 连接 URL
        ttl: 历史过期时间（秒），默认 24 小时
        distance_threshold: 语义检索距离阈值
        vectorizer: 向量化器（用于语义检索），不传则 fallback 到文本匹配
        connection_kwargs: Redis 连接附加参数
    """

    def __init__(
        self,
        name: str,
        redis_url: str = "redis://localhost:6379",
        ttl: int = 86400,
        distance_threshold: float = 0.3,
        vectorizer=None,
        connection_kwargs: Optional[Dict[str, Any]] = None,
    ):
        self.name = name

        try:
            self._history = _RedisVLSemanticMessageHistory(
                name=name,
                redis_url=redis_url,
                distance_threshold=distance_threshold,
                vectorizer=vectorizer,
                connection_kwargs=connection_kwargs or {},
            )
            logger.info(
                "SemanticMessageHistory '%s' initialized (threshold=%.2f)",
                name,
                distance_threshold,
            )
        except Exception as e:
            logger.error("Failed to initialize SemanticMessageHistory '%s': %s", name, e)
            raise

    # ---- 写操作 ----

    def add_message(
        self,
        message: Dict[str, str],
        session_tag: Optional[str] = None,
    ) -> None:
        """添加单条消息到对话历史

        Args:
            message: 消息字典，格式为 {"role": "...", "content": "..."}
                     支持 role: system, user, llm, tool
                     可选字段: metadata (dict)
            session_tag: 会话标签，用于多轮对话分组
        """
        try:
            self._history.add_message(message=message, session_tag=session_tag)
            logger.debug("Added message: role=%s content='%s'", message.get("role"), message.get("content", "")[:30])
        except Exception as e:
            logger.error("Failed to add message: %s", e)
            raise RuntimeError(f"Failed to add message: {e}") from e

    def add_messages(
        self,
        messages: List[Dict[str, str]],
        session_tag: Optional[str] = None,
    ) -> None:
        """批量添加消息到对话历史

        Args:
            messages: 消息字典列表
            session_tag: 会话标签
        """
        try:
            self._history.add_messages(messages=messages, session_tag=session_tag)
            logger.debug("Added %d messages", len(messages))
        except Exception as e:
            logger.error("Failed to add messages: %s", e)
            raise RuntimeError(f"Failed to add messages: {e}") from e

    def store(
        self,
        prompt: str,
        response: str,
        session_tag: Optional[str] = None,
    ) -> None:
        """快速存储一问一答对（简化接口）

        Args:
            prompt: 用户提问
            response: LLM 回答
            session_tag: 会话标签
        """
        self.add_messages(
            [
                {"role": "user", "content": prompt},
                {"role": "llm", "content": response},
            ],
            session_tag=session_tag,
        )

    # ---- 读操作 ----

    def get_recent(
        self,
        top_k: int = 10,
        as_text: bool = False,
        raw: bool = False,
        session_tag: Optional[str] = None,
        role: Optional[Union[str, List[str]]] = None,
    ) -> Union[List[str], List[Dict[str, str]]]:
        """获取最近的对话历史

        Args:
            top_k: 返回最近几条记录
            as_text: 是否仅返回文本内容
            raw: 是否返回原始数据（含 metadata）
            session_tag: 会话标签过滤
            role: 按角色过滤（如 "user" 或 ["user", "llm"]）

        Returns:
            消息列表（dict 或 str，取决于 as_text）
        """
        try:
            return self._history.get_recent(
                top_k=top_k,
                as_text=as_text,
                raw=raw,
                session_tag=session_tag,
                role=role,
            )
        except Exception as e:
            logger.error("Failed to get recent history: %s", e)
            return []

    def get_relevant(
        self,
        prompt: str,
        as_text: bool = False,
        top_k: int = 5,
        fall_back: bool = False,
        session_tag: Optional[str] = None,
        raw: bool = False,
        distance_threshold: Optional[float] = None,
        role: Optional[Union[str, List[str]]] = None,
    ) -> Union[List[str], List[Dict[str, str]]]:
        """语义检索相关的历史消息

        通过语义向量相似度找到与当前提问相关的历史对话。

        Args:
            prompt: 当前提问文本
            as_text: 是否仅返回文本
            top_k: 返回条数
            fall_back: 向量检索无结果时是否回退到关键词匹配
            session_tag: 会话过滤
            raw: 是否返回原始数据
            distance_threshold: 临时覆盖阈值
            role: 按角色过滤

        Returns:
            匹配的消息列表
        """
        try:
            return self._history.get_relevant(
                prompt=prompt,
                as_text=as_text,
                top_k=top_k,
                fall_back=fall_back,
                session_tag=session_tag,
                raw=raw,
                distance_threshold=distance_threshold,
                role=role,
            )
        except Exception as e:
            logger.error("Failed to get relevant history: %s", e)
            return []

    def count(self, session_tag=None) -> int:
        """统计对话历史中的消息数量

        Args:
            session_tag: 会话过滤

        Returns:
            消息总数
        """
        try:
            return self._history.count(session_tag=session_tag)
        except Exception as e:
            logger.error("Failed to count history: %s", e)
            return 0

    # ---- 维护 ----

    def clear(self) -> None:
        """清空当前 session 的所有对话历史"""
        try:
            self._history.clear()
            logger.info("History '%s' cleared", self.name)
        except Exception as e:
            logger.error("Failed to clear history: %s", e)
            raise RuntimeError(f"Failed to clear history: {e}") from e

    def delete(self) -> None:
        """删除整个 history 索引和数据"""
        try:
            self._history.delete()
            logger.info("History '%s' deleted", self.name)
        except Exception as e:
            logger.error("Failed to delete history: %s", e)
            raise RuntimeError(f"Failed to delete history: {e}") from e

    def drop(self, id: Optional[str] = None) -> None:
        """删除特定消息

        Args:
            id: 消息 ID，不传则清空所有
        """
        try:
            self._history.drop(id=id)
        except Exception as e:
            logger.error("Failed to drop history: %s", e)

    def set_distance_threshold(self, threshold: float) -> None:
        """动态调整语义检索阈值

        Args:
            threshold: 新的阈值 [0, 1]
        """
        self._history.set_distance_threshold(threshold)
        logger.info("Distance threshold updated to %.2f", threshold)

    # ---- 兼容旧接口 ----

    def get_history(self) -> List[Dict[str, str]]:
        """兼容旧接口：获取全部历史"""
        return self.get_recent(top_k=1000, raw=True)  # type: ignore

    def clear_history(self) -> Any:
        """兼容旧接口：清空历史"""
        self.clear()

    def delete_history(self, top_k: int = 10) -> None:
        """兼容旧接口：删除最近的 top_k 条"""
        current = self.get_recent(top_k=1000, raw=True)
        if not isinstance(current, list):
            return
        keep = current[:-top_k] if len(current) > top_k else []
        self.clear()
        if keep:
            self.add_messages(keep)

    def __repr__(self) -> str:
        return f"SemanticMessageHistory(name='{self.name}')"
