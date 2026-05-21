"""
FastAPI 接口服务
提供知识库CRUD、文档上传、多模态问答三个核心功能

启动方式: uvicorn api:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import json
import uuid
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from kafka import KafkaProducer
from sentence_transformers import SentenceTransformer
from pymilvus import MilvusClient

from orm_model import File, KnowledgeBase, Session as OrmSession

# ============================================================
# 全局资源（生命周期管理）
# ============================================================
bge_model: Optional[SentenceTransformer] = None
milvus_client: Optional[MilvusClient] = None
qwen_client = None  # openai.OpenAI 实例


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bge_model, milvus_client, qwen_client

    # --- 启动时加载模型 ---
    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

    import openai
    bge_model = SentenceTransformer('/root/autodl-tmp/models/BAAI/bge-small-zh-v1.5')
    print("[API] BGE model loaded.")

    milvus_client = MilvusClient(
        uri="https://in03-5cb3b56f3af9ebc.serverless.ali-cn-hangzhou.cloud.zilliz.com.cn",
        token="9027d285f74e5ce113bf24162fc5cabe04b67db3ee25055f4748ea23785f00d0fa9b8217c108a04dc77c4a703b5860a7d39d7a7b"
    )
    print("[API] Milvus connected.")

    qwen_client = openai.OpenAI(
        api_key="sk-711c186f74494136ba26035be25a7cb8",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    print("[API] Qwen client ready.")

    yield

    print("[API] Shutting down.")


app = FastAPI(
    title="多模态RAG问答 - API",
    description="知识库管理 | 文档上传 | 多模态问答",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Pydantic 请求/响应模型
# ============================================================

class KBCreateRequest(BaseModel):
    name: str
    description: str = ""

class KBUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class KBResponse(BaseModel):
    id: int
    name: str
    description: str
    created_at: str

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    query: str
    kb_id: Optional[int] = None
    top_k: int = 5

class SourceItem(BaseModel):
    text: str
    file_name: str
    db_id: int

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem]


# ============================================================
# 1. 知识库 CRUD
# ============================================================

@app.get("/knowledge_base", response_model=List[KBResponse])
def list_knowledge_bases():
    """获取所有知识库列表"""
    with OrmSession() as session:
        kbs = session.query(KnowledgeBase).all()
        return [
            KBResponse(
                id=kb.id,
                name=kb.name,
                description=kb.description or "",
                created_at=kb.created_at.strftime("%Y-%m-%d %H:%M:%S") if kb.created_at else "",
            )
            for kb in kbs
        ]


@app.get("/knowledge_base/{kb_id}", response_model=KBResponse)
def get_knowledge_base(kb_id: int):
    """获取单个知识库详情"""
    with OrmSession() as session:
        kb = session.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        return KBResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description or "",
            created_at=kb.created_at.strftime("%Y-%m-%d %H:%M:%S") if kb.created_at else "",
        )


@app.post("/knowledge_base", response_model=KBResponse, status_code=201)
def create_knowledge_base(req: KBCreateRequest):
    """创建知识库"""
    with OrmSession() as session:
        exists = session.query(KnowledgeBase).filter(
            KnowledgeBase.name == req.name
        ).first()
        if exists:
            raise HTTPException(status_code=400, detail=f"知识库 '{req.name}' 已存在")

        kb = KnowledgeBase(name=req.name, description=req.description)
        session.add(kb)
        session.commit()
        session.refresh(kb)

        return KBResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description or "",
            created_at=kb.created_at.strftime("%Y-%m-%d %H:%M:%S") if kb.created_at else "",
        )


@app.put("/knowledge_base/{kb_id}", response_model=KBResponse)
def update_knowledge_base(kb_id: int, req: KBUpdateRequest):
    """更新知识库信息"""
    with OrmSession() as session:
        kb = session.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        if req.name is not None:
            dup = session.query(KnowledgeBase).filter(
                KnowledgeBase.name == req.name, KnowledgeBase.id != kb_id
            ).first()
            if dup:
                raise HTTPException(status_code=400, detail=f"知识库 '{req.name}' 已存在")
            kb.name = req.name
        if req.description is not None:
            kb.description = req.description

        session.commit()
        session.refresh(kb)

        return KBResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description or "",
            created_at=kb.created_at.strftime("%Y-%m-%d %H:%M:%S") if kb.created_at else "",
        )


@app.delete("/knowledge_base/{kb_id}")
def delete_knowledge_base(kb_id: int):
    """删除知识库（级联：删除关联文档本地文件 + Milvus向量 + 数据库记录）"""
    with OrmSession() as session:
        kb = session.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        files = session.query(File).filter(File.kb_id == kb_id).all()
        for f in files:
            # 删除Milvus向量
            try:
                milvus_client.delete(
                    collection_name="rag_data_new",
                    filter=f"db_id == {f.id}",
                )
            except Exception as e:
                print(f"[WARN] Milvus delete failed for file {f.id}: {e}")
            # 删除本地文件
            if os.path.exists(f.filepath):
                os.remove(f.filepath)
            session.delete(f)

        session.delete(kb)
        session.commit()

    return {"message": f"知识库 '{kb.name}' 已删除"}


# ============================================================
# 2. POST /upload/document — 上传文档
# ============================================================

@app.post("/upload/document", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    kb_id: Optional[int] = Form(None),
):
    """
    上传文档到指定知识库（可选kb_id，不传则上传到公共区）。
    文件保存到本地 uploads/ 目录，并通过 Kafka 触发离线解析。
    """
    # 验证知识库存在
    if kb_id is not None:
        with OrmSession() as session:
            kb = session.query(KnowledgeBase).filter(
                KnowledgeBase.id == kb_id
            ).first()
            if not kb:
                raise HTTPException(status_code=404, detail="知识库不存在")

    # 保存文件
    ext = os.path.splitext(file.filename)[1]
    save_name = str(uuid.uuid4()) + ext
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, save_name)

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    # 写入数据库
    with OrmSession() as session:
        record = File(
            filename=file.filename,
            filepath=save_path,
            filestate="已上传",
            kb_id=kb_id,
        )
        session.add(record)
        session.flush()
        file_id = record.id
        session.commit()

    # 发送 Kafka 消息，触发离线解析
    try:
        producer = KafkaProducer(
            bootstrap_servers="localhost:9092",
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        producer.send(
            "rag-data",
            value={
                "file_name": file.filename,
                "file_path": save_path,
                "id": file_id,
            },
        )
        producer.flush()
    except Exception as e:
        print(f"[WARN] Kafka 发送失败: {e}")

    return {
        "message": "文件上传成功，已加入解析队列",
        "file_id": file_id,
        "filename": file.filename,
        "kb_id": kb_id,
    }


# ============================================================
# 3. POST /chat — 多模态问答
# ============================================================

RAG_PROMPT_TEMPLATE = """基于资料回答的提问提问问题：{query}

相关资料: {context}

回答要求：
- 回答要客观，有逻辑，要基于只有的资料。
- 如果资料中包含图片链接，则单独一行进行输出，保留图的原始链接，需要将图放在合适的相关内容的位置。"""


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    多模态问答接口

    流程：
    1. BGE 编码用户提问
    2. 在 Milvus 中检索相关 chunk（支持按 kb_id 过滤）
    3. 拼装 RAG Prompt
    4. Qwen-VL 生成回答
    """
    if not bge_model or not milvus_client or not qwen_client:
        raise HTTPException(status_code=503, detail="模型资源尚未加载完成，请稍后重试")

    # ---- 1. 提问向量化 ----
    query_embedding = bge_model.encode(req.query, normalize_embeddings=True)

    # ---- 2. 构建检索参数 ----
    search_params = {
        "collection_name": "rag_data_new",
        "data": [list(query_embedding)],
        "limit": req.top_k,
        "anns_field": "text_vector",
        "output_fields": ["text", "db_id", "file_name", "file_path"],
    }

    # 如果指定了知识库，通过文件ID做白名单过滤
    if req.kb_id is not None:
        with OrmSession() as session:
            file_ids = [
                row[0]
                for row in session.query(File.id)
                .filter(File.kb_id == req.kb_id)
                .all()
            ]

        if not file_ids:
            return ChatResponse(answer="该知识库下暂无已解析的文档。", sources=[])

        search_params["filter"] = (
            f"db_id in [{','.join(str(fid) for fid in file_ids)}]"
        )

    # ---- 3. Milvus 检索 ----
    results = milvus_client.search(**search_params)

    if not results or not results[0]:
        return ChatResponse(answer="未检索到相关资料。", sources=[])

    # ---- 4. 拼装上下文 & 来源 ----
    related_content = ""
    sources = []
    for result in results[0]:
        entity = result["entity"]
        file_dir = os.path.basename(entity["file_path"]).split(".")[0]
        text = entity["text"].replace(
            "images/",
            f"./processed/{file_dir}/vlm/images/",
        )
        related_content += text + "\n"

        sources.append(SourceItem(
            text=entity["text"][:200],
            file_name=entity["file_name"],
            db_id=entity["db_id"],
        ))

    # ---- 5. Qwen-VL 生成回答 ----
    prompt = RAG_PROMPT_TEMPLATE.format(query=req.query, context=related_content)
    completion = qwen_client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )

    return ChatResponse(
        answer=completion.choices[0].message.content,
        sources=sources,
    )


# ============================================================
# 健康检查
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "bge_loaded": bge_model is not None,
        "milvus_connected": milvus_client is not None,
        "qwen_ready": qwen_client is not None,
    }
