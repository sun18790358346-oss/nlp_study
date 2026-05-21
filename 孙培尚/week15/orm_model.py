# file_manager.py
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class KnowledgeBase(Base):
    """知识库表"""
    __tablename__ = 'knowledge_bases'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)  # 知识库名称
    description = Column(String(1000), default="")  # 描述
    created_at = Column(DateTime, default=datetime.now)  # 创建时间


class File(Base):
    """文件表 - 核心文件管理系统"""
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)  # 文件名
    filepath = Column(String(1000), nullable=False)  # 完整路径
    filestate = Column(String(20), nullable=False)  # 处理状态
    kb_id = Column(Integer, nullable=True)  # 关联知识库ID

    __table_args__ = (
        {'sqlite_autoincrement': True}
    )


db_path = os.path.join(os.getcwd(), 'db.db')
engine = create_engine(f'sqlite:///{db_path}')
Base.metadata.create_all(engine)

# 迁移：为已有 files 表添加 kb_id 列（若不存在）
inspector = inspect(engine)
if 'files' in inspector.get_table_names():
    columns = [col['name'] for col in inspector.get_columns('files')]
    if 'kb_id' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE files ADD COLUMN kb_id INTEGER"))
            conn.commit()

Session = sessionmaker(bind=engine)
