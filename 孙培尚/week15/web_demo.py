import streamlit as st
from PIL import Image
import io


pg = st.navigation([
    st.Page("web_page_upload.py", title="文件管理"),
    st.Page("web_page_chat.py", title="图文对话"),
])
pg.run()