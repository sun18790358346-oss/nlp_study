"""
redis-vl 语义缓存完整演示

前置条件:
    1. Redis 8.x 已启动 (redis-server.exe)
    2. pip install redisvl sentence-transformers

运行:
    python -m llm_demo.demo_redisvl
"""

from llm_demo import SemanticCache
from redisvl.utils.vectorize import HFTextVectorizer


def demo_semantic_cache():
    """演示 SemanticCache 的基本用法"""
    print("=" * 60)
    print("1. 初始化向量化器（首次运行会下载模型，约 80MB）")
    print("=" * 60)

    vectorizer = HFTextVectorizer(
        model="sentence-transformers/all-MiniLM-L6-v2"
    )

    print("2. 初始化语义缓存")
    cache = SemanticCache(
        name="llmcache",
        redis_url="redis://localhost:6379",
        distance_threshold=0.15,
        vectorizer=vectorizer,
    )

    # 先清空
    cache.clear()

    print("\n3. 存储问答对到缓存")
    pairs = [
        ("法国的首都是什么？", "巴黎"),
        ("中国的首都是什么？", "北京"),
        ("今天天气怎么样？", "晴天，温度25°C"),
    ]
    for q, a in pairs:
        key = cache.store(prompt=q, response=a)
        print(f"   存储: '{q}' → '{a}'  (key={key})")

    print("\n4. 语义相似查询（精确匹配）")
    result = cache.check(prompt="法国的首都是什么？")
    if result:
        print(f"   命中! 回答: {result[0]['response']}")

    print("\n5. 语义相似查询（模糊匹配）")
    test_queries = [
        "法国首都",
        "中国首都",
        "天气如何",
        "美国首都是什么",  # 未存储，应不命中
    ]
    for q in test_queries:
        result = cache.check(prompt=q)
        if result:
            distance = result[0].get("distance", "N/A")
            print(f"   ✅ '{q}' → 命中: {result[0]['response']} (距离={distance:.4f})")
        else:
            print(f"   ❌ '{q}' → 未命中")

    print("\n✅ 演示完成!")


if __name__ == "__main__":
    demo_semantic_cache()
