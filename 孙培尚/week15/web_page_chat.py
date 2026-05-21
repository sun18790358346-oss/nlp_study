import streamlit as st
import openai

import streamlit as st
import re

qwen_client = openai.OpenAI(
    api_key="sk-711c186f74494136ba26035be25a7cb8",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

rag_prompt = """基于资料回答的提问提问问题：{0}

相关资料: {1}

回答要求：
- 回答要客观，有逻辑，要基于只有的资料。
- 如果资料中包含图片链接，则单独一行进行输出，保留图的原始链接，需要将图放在合适的相关内容的位置。
"""

def clear_chat_history():
    st.session_state.messages = [
        {"role": "system", "content": "你好，我是AI助手，可以直接与大模型对话 也 可以调用内部工具。"}
    ]
    st.session_state.session_id = None


if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {"role": "system", "content": "你好，我是AI助手，可以直接与大模型对话 也 可以调用内部工具。"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

with st.sidebar:
    st.button('清空当前聊天', on_click=clear_chat_history, use_container_width=True)

import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
from sentence_transformers import SentenceTransformer

bge_model = SentenceTransformer('/root/autodl-tmp/models/BAAI/bge-small-zh-v1.5')
print("Loading beg started!")

from pymilvus import MilvusClient  # milvus客户端
client = MilvusClient(
    uri="https://in03-5cb3b56f3af9ebc.serverless.ali-cn-hangzhou.cloud.zilliz.com.cn",
    token="9027d285f74e5ce113bf24162fc5cabe04b67db3ee25055f4748ea23785f00d0fa9b8217c108a04dc77c4a703b5860a7d39d7a7b"
)




# 在 Streamlit 应用中显示 Markdown 内容，同时处理图片
def render_markdown_with_images(markdown_text):
    # 匹配 Markdown 图片语法 ![alt text](image_url)
    pattern = re.compile(r'!\[.*?\]\((.*?)\)')

    # 记录上一个位置
    last_pos = 0

    # 查找所有匹配项
    for match in pattern.finditer(markdown_text):
        # 显示上一个位置到匹配位置之间的文本
        st.markdown(markdown_text[last_pos:match.start()], unsafe_allow_html=True)

        # 显示图片
        img_url = match.group(1)
        st.image(img_url)

        # 更新上一个位置
        last_pos = match.end()

    # 显示剩余的文本
    st.markdown(markdown_text[last_pos:], unsafe_allow_html=True)



if prompt := st.chat_input(accept_file="multiple", file_type=["txt", "pdf", "jpg", "png", "jpeg", "doc", "docx"]):
    st.session_state.messages.append({"role": "user", "content": prompt.text})

    with st.chat_message("user"):  # 用户输入
        st.markdown(prompt.text)

    with st.chat_message("assistant"):  # 大模型输出
        prompt_embedding = bge_model.encode(prompt.text, normalize_embeddings=True)

        results = client.search(
            collection_name="rag_data_new",
            data=[list(prompt_embedding)],
            limit=5,
            anns_field="text_vector",
            output_fields=["text", "db_id", "file_name", "file_path"]
        )

        related_content = ""
        for result in results[0]:
            file_dir = os.path.basename(result["entity"]["file_path"]).split(".")[0]
            result["entity"]["text"] = result["entity"]["text"].replace("images/", "./processed/" + file_dir + "/vlm/images/")

            related_content += result["entity"]["text"] + "\n"

        completion = qwen_client.chat.completions.create(
            model="qwen-plus",
            messages=[{'role': 'system', 'content': 'You are a helpful assistant.'},
                      {'role': 'user', 'content': rag_prompt.format(prompt.text, "\n".join(related_content))}],
        )

        render_markdown_with_images(completion.choices[0].message.content)
