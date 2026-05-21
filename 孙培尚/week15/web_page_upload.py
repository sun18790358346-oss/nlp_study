import os
import streamlit as st
from orm_model import File, Session
import uuid
from kafka import KafkaProducer
import json
from pymilvus import MilvusClient  # milvus客户端

client = MilvusClient(
    uri="https://in03-5cb3b56f3af9ebc.serverless.ali-cn-hangzhou.cloud.zilliz.com.cn",
    token="9027d285f74e5ce113bf24162fc5cabe04b67db3ee25055f4748ea23785f00d0fa9b8217c108a04dc77c4a703b5860a7d39d7a7b"
)

def query_files():
    """查询所有文件并展示，每个文件旁边添加删除按钮"""
    with Session() as session:
        files = session.query(File).all()
    
    if files:
        for file in files:
            # 创建一个删除按钮，按钮的 key 是文件的 ID
            delete_button = st.button(f"删除 {file.filename}", key=file.id)
            
            # 如果用户点击了删除按钮
            if delete_button:
                delete_file(file.id)
                
            # 展示文件信息
            st.write(file)
    else:
        st.warning("没有找到任何文件记录。")


def delete_file(id):
    global uploaded_file
    uploaded_file = None
    with Session() as session:
        file = session.query(File).filter(File.id == id).first()
        if file:
            session.delete(file)
            session.commit()
            st.success("文件删除成功")
            os.remove(file.filepath)
        else:
            st.error("文件不存在")

    client.delete(collection_name="rag_data_new", filter=f"db_id == {id}")

st.markdown("### 文件管理")

query_files()


st.markdown("### 文件上传")

uploaded_file = st.file_uploader("上传文件", type=["pdf", "docx", "txt"])
if uploaded_file is not None:
    file_name = uploaded_file.name
    file_extension = os.path.splitext(file_name)[1]
    save_name = str(uuid.uuid4())
    if not os.path.exists("uploads"):
        os.makedirs("uploads", exist_ok=True)

    save_path = os.path.join("uploads", save_name) + file_extension

    with open(save_path, "wb") as f:
        f.write(uploaded_file.getvalue())

    with Session() as session:
        record = File(
            filename=file_name,
            filepath=save_path,
            filestate="已上传"
        )
        
        session.add(record)
        session.flush()
        record.id = record.id
        session.commit()

        producer = KafkaProducer(
                bootstrap_servers="localhost:9092",
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        producer.send(
            "rag-data", 
            value={"file_name": file_name, "file_path": save_path, "id": record.id}
        )
        producer.flush()
