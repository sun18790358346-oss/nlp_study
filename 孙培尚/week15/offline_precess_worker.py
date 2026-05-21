import os
import glob
import traceback

from kafka import KafkaConsumer
import json
import numpy as np
import subprocess
from pymilvus import MilvusClient  # milvus客户端

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
from sentence_transformers import SentenceTransformer

bge_model = SentenceTransformer('/root/autodl-tmp/models/BAAI/bge-small-zh-v1.5')
print("Loading beg started!")

clip_model = SentenceTransformer(
    '/root/autodl-tmp/models/jinaai/jina-clip-v2', trust_remote_code=True, truncate_dim=1024
)
print("Loading clip started!")

client = MilvusClient(
    uri="https://in03-5cb3b56f3af9ebc.serverless.ali-cn-hangzhou.cloud.zilliz.com.cn",
    token="9027d285f74e5ce113bf24162fc5cabe04b67db3ee25055f4748ea23785f00d0fa9b8217c108a04dc77c4a703b5860a7d39d7a7b"
)


def split_text2chunks(lines, chunk_size=256):
    """
    将文本分割成多个块，每个块的长度不超过chunk_size个字符
    """
    chunks = []
    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line == "# References":
            continue

        if len(line) > 2:
            if line[0] == "[" and line[1].isdigit():
                continue

        if len(chunks) == 0:
            chunks.append(line)
        else:
            if len(chunks[-1]) <= chunk_size:
                chunks[-1] += "\n" + line
            else:
                chunks.append(line)

    return chunks


def encode_text_and_image(text, markdown_path):
    """
    将文本编码成向量
    """
    text_with_no_image = "\n".join([line for line in text.split("\n") if not line.startswith("![")])
    text_with_image = [line for line in text.split("\n") if line.startswith("![")]

    try:
        text_bge_embedding = bge_model.encode(text_with_no_image, normalize_embeddings=True)
        text_bge_embedding = list(text_bge_embedding)
    except:
        traceback.print_exc()
        text_bge_embedding = np.zeros(512)

    try:
        text_clip_embedding = clip_model.encode(text_with_no_image, normalize_embeddings=True)
        text_clip_embedding = list(text_clip_embedding)
    except:
        traceback.print_exc()
        text_clip_embedding = np.zeros(1024)

    if len(text_with_image) > 0:
        image_path = text_with_image[0].split("](")[1].split(")")[0]
        image_real_path = os.path.dirname(markdown_path) + image_path.split("/")[-1]
        try:
            print(f"Encoding {image_real_path}")
            image_clip_embedding = clip_model.encode(image_real_path, normalize_embeddings=True)
            image_clip_embedding = list(image_clip_embedding)
        except:
            traceback.print_exc()
            image_clip_embedding = np.zeros(1024)
    else:
        image_clip_embedding = np.zeros(1024)

    return text_bge_embedding, text_clip_embedding, image_clip_embedding


def encode_document(path, file_id, file_name, file_path):
    lines = open(path, 'r', encoding='utf-8').readlines()
    chunks = split_text2chunks(lines)
    for chunk in chunks:
        try:
            text_bge_embedding, text_clip_embedding, image_clip_embedding = encode_text_and_image(
                chunk,
                path
            )

            data = [
                {
                    "text_vector": text_bge_embedding,
                    "clip_text_vector": text_clip_embedding,
                    "clip_image_vector": image_clip_embedding,
                    "text": chunk,
                    "db_id": file_id,
                    "file_name": file_name,
                    "file_path": file_path
                }
            ]
            insert_result = client.insert(
                collection_name="rag_data_new",
                data=data
            )
        except:
            traceback.print_exc()


consumer = KafkaConsumer(
    "rag-data",
    bootstrap_servers="localhost:9092",
    enable_auto_commit=True,  # 自动提交offset
    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
)


def main():
    for msg in consumer:
        try:
            # 步骤1，获取文件信息
            print(msg.value)
            file_name = msg.value['file_name']
            file_path = msg.value['file_path']
            file_id = msg.value['id']

            if not os.path.exists(file_path):
                continue

            # 步骤2，使用mineru解析文件
            print(f"mineru -p {file_path} -o ./precessed -b vlm-http-client -u http://127.0.0.1:30000")
            subprocess.check_output(f"mineru -p {file_path} -o ./precessed -b vlm-http-client -u http://127.0.0.1:30000",
                                    shell=True, timeout=600)

            # 步骤3，使用bge和clip编码
            markdown_file_paths = glob.glob(os.path.join("./processed", os.path.basename(file_path).split(".")[0]) + "/**/**.md")
            # image_file_paths = glob.glob(os.path.join("./precessed", file_name) + "/**/**.jpg")

            if len(markdown_file_paths) == 0:
                print(f"Failed to find {file_name}")
                continue

            encode_document(markdown_file_paths[0], file_id, file_name, file_path)

        except Exception as e:
            print(e)

if __name__ == "__main__":
    main()

    # file_name = "2309 vllm.pdf"
    # markdown_file_paths = glob.glob(os.path.join("./precessed", file_name.split(".")[0]) + "/**/**.md")
    # encode_document(markdown_file_paths[0], -1)