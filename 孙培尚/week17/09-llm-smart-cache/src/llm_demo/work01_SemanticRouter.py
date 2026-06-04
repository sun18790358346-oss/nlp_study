"""
SemanticRouter — 语义意图路由组件

基于 redis-vl 的 SemanticRouter，通过语义相似度实现自然语言的意图识别和路由。
用户提问后自动匹配预定义的 Route，路由到对应的处理逻辑。

用法示例:
    from llm_cache import SemanticRouter, Route

    routes = [
        Route(
            name="greeting",
            references=["你好", "hello", "hi"],
            metadata={"type": "greeting", "handler": "greeting_handler"},
            distance_threshold=0.3,
        ),
        Route(
            name="refund",
            references=["退货", "退款", "如何退货"],
            metadata={"type": "after_sales"},
            distance_threshold=0.25,
        ),
    ]

    router = SemanticRouter(
        name="topic-router",
        routes=routes,
        redis_url="redis://localhost:6379",
    )

    result = router.route("你好，早上好")
    print(result[0].name)  # "greeting"
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from redisvl.extensions.router import (
    Route as _RedisVLRoute,
    SemanticRouter as _RedisVLSemanticRouter,
)

logger = logging.getLogger(__name__)


class Route:
    """路由定义

    定义一个意图分类，包含类别名、参考示例和匹配阈值。

    Args:
        name: 路由/类别名称
        references: 参考示例文本列表（用于生成语义向量）
        metadata: 附加元数据（可选），如 handler 函数名、type 等
        distance_threshold: 匹配距离阈值 [0, 1]，越小越严格
    """

    def __init__(
        self,
        name: str,
        references: List[str],
        metadata: Optional[Dict[str, Any]] = None,
        distance_threshold: float = 0.3,
    ):
        self.name = name
        self.references = references
        self.metadata = metadata or {}
        self.distance_threshold = distance_threshold

    def _to_redisvl(self) -> _RedisVLRoute:
        """转换为 redis-vl 的 Route 对象"""
        return _RedisVLRoute(
            name=self.name,
            references=self.references,
            metadata=self.metadata,
            distance_threshold=self.distance_threshold,
        )

    @classmethod
    def _from_redisvl(cls, route: _RedisVLRoute) -> "Route":
        """从 redis-vl 的 Route 对象创建"""
        return cls(
            name=route.name,
            references=list(route.references),
            metadata=route.metadata,
            distance_threshold=route.distance_threshold,
        )

    def __repr__(self) -> str:
        return (
            f"Route(name='{self.name}', "
            f"refs={len(self.references)}, "
            f"threshold={self.distance_threshold})"
        )


class SemanticRouter:
    """语义意图路由器

    基于语义向量匹配的自然语言意图路由。用户提问后，
    通过向量相似度匹配最合适的 Route，返回匹配结果。

    Args:
        name: 路由器名称
        routes: Route 列表
        redis_url: Redis 连接 URL
        vectorizer: 向量化器实例
        connection_kwargs: Redis 连接附加参数
        overwrite: 同名路由器是否重建索引
    """

    def __init__(
        self,
        name: str,
        routes: List[Route],
        redis_url: str = "redis://localhost:6379",
        vectorizer=None,
        connection_kwargs: Optional[Dict[str, Any]] = None,
        overwrite: bool = False,
    ):
        self.name = name

        # 转换为 redis-vl 的 Route 对象
        _routes = [r._to_redisvl() for r in routes]

        try:
            self._router = _RedisVLSemanticRouter(
                name=name,
                routes=_routes,
                redis_url=redis_url,
                vectorizer=vectorizer,
                connection_kwargs=connection_kwargs or {},
                overwrite=overwrite,
            )
            logger.info(
                "SemanticRouter '%s' initialized with %d routes",
                name,
                len(routes),
            )
        except Exception as e:
            logger.error("Failed to initialize SemanticRouter '%s': %s", name, e)
            raise

    # ---- 路由 ----

    def route(
        self,
        statement: str,
        max_k: Optional[int] = None,
        distance_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """路由一条用户输入到匹配的意图

        Args:
            statement: 用户输入文本
            max_k: 最多返回几条匹配结果
            distance_threshold: 临时覆盖全局阈值

        Returns:
            匹配结果列表，每条包含:
            - name: 路由名称
            - distance: 语义距离
            - metadata: 路由元数据
        """
        try:
            matches = self._router.route_many(
                statement=statement,
                max_k=max_k,
                distance_threshold=distance_threshold,
            )
            results = []
            for m in matches:
                results.append({
                    "name": m.name,
                    "distance": m.distance if hasattr(m, "distance") else 0.0,
                    "metadata": m.metadata if hasattr(m, "metadata") else {},
                })
            return results
        except Exception as e:
            logger.error("Failed to route statement '%s': %s", statement[:30], e)
            return []

    def route_many(
        self,
        statement: Optional[str] = None,
        vector: Optional[List[float]] = None,
        max_k: Optional[int] = None,
        distance_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """路由（高级接口，支持自定义向量）

        Args:
            statement: 输入文本
            vector: 直接传入向量（与 statement 二选一）
            max_k: 最大返回数
            distance_threshold: 阈值覆盖

        Returns:
            匹配结果列表
        """
        return self.route(
            statement=statement or "",
            max_k=max_k,
            distance_threshold=distance_threshold,
        )

    def __call__(self, statement: str) -> List[Dict[str, Any]]:
        """快捷调用，等价于 route()

        Args:
            statement: 用户输入

        Returns:
            匹配结果列表
        """
        return self.route(statement)

    # ---- 路由管理 ----

    def add_route(self, route: Route) -> None:
        """添加新路由

        Args:
            route: Route 对象
        """
        try:
            self._router.add_route_references(
                route_name=route.name,
                references=route.references,
            )
            logger.info("Added route '%s'", route.name)
        except Exception as e:
            logger.error("Failed to add route '%s': %s", route.name, e)
            raise RuntimeError(f"Failed to add route: {e}") from e

    def add_route_references(
        self, route_name: str, references: str | List[str]
    ) -> List[str]:
        """为已有路由添加参考示例

        Args:
            route_name: 路由名称
            references: 新增的参考文本

        Returns:
            添加的 reference IDs
        """
        try:
            return self._router.add_route_references(
                route_name=route_name,
                references=references,
            )
        except Exception as e:
            logger.error("Failed to add references to route '%s': %s", route_name, e)
            return []

    def remove_route(self, route_name: str) -> None:
        """删除路由

        Args:
            route_name: 路由名称
        """
        try:
            self._router.remove_route(route_name=route_name)
            logger.info("Removed route '%s'", route_name)
        except Exception as e:
            logger.error("Failed to remove route '%s': %s", route_name, e)

    def get_route(self, route_name: str) -> Optional[Route]:
        """获取路由详情

        Args:
            route_name: 路由名称

        Returns:
            Route 对象，不存在返回 None
        """
        try:
            route = self._router.get(route_name=route_name)
            if route:
                return Route._from_redisvl(route)
            return None
        except Exception as e:
            logger.error("Failed to get route '%s': %s", route_name, e)
            return None

    def get_route_references(
        self, route_name: str = ""
    ) -> List[Dict[str, Any]]:
        """获取路由的参考示例

        Args:
            route_name: 路由名称

        Returns:
            参考示例列表
        """
        try:
            return self._router.get_route_references(route_name=route_name)
        except Exception as e:
            logger.error("Failed to get references: %s", e)
            return []

    def update_route_thresholds(
        self, route_thresholds: Dict[str, Optional[float]]
    ) -> None:
        """批量更新路由阈值

        Args:
            route_thresholds: {路由名: 新阈值} 字典
        """
        try:
            self._router.update_route_thresholds(route_thresholds=route_thresholds)
            logger.info("Route thresholds updated: %s", route_thresholds)
        except Exception as e:
            logger.error("Failed to update thresholds: %s", e)

    # ---- 维护 ----

    def clear(self) -> None:
        """清空所有路由数据"""
        try:
            self._router.clear()
            logger.info("Router '%s' cleared", self.name)
        except Exception as e:
            logger.error("Failed to clear router: %s", e)
            raise RuntimeError(f"Failed to clear router: {e}") from e

    def delete(self) -> None:
        """删除整个路由器索引"""
        try:
            self._router.delete()
            logger.info("Router '%s' deleted", self.name)
        except Exception as e:
            logger.error("Failed to delete router: %s", e)
            raise RuntimeError(f"Failed to delete router: {e}") from e

    def __repr__(self) -> str:
        return f"SemanticRouter(name='{self.name}')"
