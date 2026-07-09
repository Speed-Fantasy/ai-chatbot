"""
文档处理 Agent — Streamlit 应用
上传文档 → Agent 自主选择工具 → 分析/总结/提取/改写
"""
import os
import sys
import json
import streamlit as st
from openai import OpenAI

# 路径
BASE_DIR = os.path.dirname(__file__)
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
CHROMA_DB_PATH = os.path.join(BASE_DIR, "chroma_db")

# 引入 RAG + Agent
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)

# week06 自身必须在最前面，否则 from tools 会找到 week04
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

_week03 = os.path.join(_parent_dir, "week03")
if _week03 not in sys.path:
    sys.path.insert(0, _week03)

from rag_core import (
    init_embedding_model, init_chroma_client, reset_chroma_db,
    extract_text, chunk_document, index_chunks,
    get_document_list, get_collection_stats, delete_document,
    DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP,
)

from tools import setup_rag, TOOL_DEFINITIONS
from agent_core import run_agent_streaming_answer

# ============================================================
# 设置
# ============================================================
COLORS = {
    "🟣 紫罗兰": "#6C63FF", "🔵 海洋蓝": "#1E90FF",
    "🟢 薄荷绿": "#00C9A7", "🟠 活力橙": "#FF6B35",
    "🔴 珊瑚红": "#FF6B6B", "🟡 琥珀金": "#F5A623",
}
TOOL_EMOJI = {
    "calculator": "🧮", "get_current_time": "🕐", "read_file": "📖",
    "list_files": "📂", "python_repl": "🐍", "write_file": "✍️",
    "search_docs": "🔍",
}
SUPPORTED_TYPES = ["txt", "pdf", "md", "py", "json", "csv", "log"]


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_settings(s):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)


# ============================================================
# 页面
# ============================================================
st.set_page_config(page_title="文档处理 Agent", page_icon="📄", layout="wide")
st.title("📄 文档处理 Agent")
st.caption("上传文档，让 AI 帮你分析、总结、提取、改写——自主决定用什么工具")

# ============================================================
# 会话状态
# ============================================================
if "client" not in st.session_state:
    st.session_state.client = OpenAI(
        api_key=st.secrets["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_messages" not in st.session_state:
    st.session_state.api_messages = []
if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()

defaults = {
    "temperature": 0.1, "max_iterations": 10,
    "chunk_size": DEFAULT_CHUNK_SIZE, "chunk_overlap": DEFAULT_CHUNK_OVERLAP,
    "user_avatar": "😎", "ai_avatar": "🤖",
    "user_name": "我", "ai_name": "Agent",
    "accent_color": "#6C63FF", "color_name": "🟣 紫罗兰",
}
saved = load_settings()
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = saved.get(k, v)

# ============================================================
# RAG 初始化
# ============================================================
@st.cache_resource
def get_rag():
    model = init_embedding_model()
    client, collection = init_chroma_client(CHROMA_DB_PATH)
    setup_rag(collection, model)
    return model, client, collection


embedding_model, chroma_client, collection = get_rag()

# ============================================================
# 侧边栏
# ============================================================
with st.sidebar:
    st.header("📁 文档管理")

    # 文档上传
    uploaded_files = st.file_uploader(
        "上传文档", type=SUPPORTED_TYPES, accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        for f in uploaded_files:
            if f.name in st.session_state.processed_files:
                continue
            text = extract_text(f, f.name)
            if not text or not text.strip():
                st.warning(f"⚠️ {f.name} 内容为空")
                continue
            with st.spinner(f"处理 {f.name}..."):
                chunks = chunk_document(text, f.name, st.session_state.chunk_size,
                                        st.session_state.chunk_overlap)
                index_chunks(chunks, collection, embedding_model)
            st.session_state.processed_files.add(f.name)
            st.toast(f"✅ {f.name} 已就绪")

    # 文档列表
    doc_list = get_document_list(collection)
    if doc_list:
        st.caption(f"已加载 {len(doc_list)} 个文档")
        for doc in doc_list:
            c1, c2 = st.columns([4, 1])
            with c1:
                st.text(f"📄 {doc}")
            with c2:
                if st.button("✕", key=f"del_{doc}"):
                    delete_document(doc, collection)
                    st.session_state.processed_files.discard(doc)
                    st.rerun()

        if st.button("🗑️ 清空文档", use_container_width=True):
            reset_chroma_db(CHROMA_DB_PATH)
            st.session_state.processed_files = set()
            st.rerun()

    st.divider()
    st.header("⚙️ 设置")

    st.session_state.temperature = st.slider("温度", 0.0, 1.5, st.session_state.temperature, 0.1)
    st.session_state.max_iterations = st.slider("最大循环", 3, 15, st.session_state.max_iterations, 1)
    st.session_state.chunk_size = st.number_input("块大小", 50, 4000, st.session_state.chunk_size, 50)
    st.session_state.chunk_overlap = st.number_input("重叠", 0, 500, st.session_state.chunk_overlap, 10)

    st.divider()

    # 新对话
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ 新对话", use_container_width=True, type="primary"):
            st.session_state.messages = []
            st.session_state.api_messages = []
            st.rerun()
    with c2:
        st.caption(f"{len(st.session_state.api_messages)//2} 轮")

    st.divider()

    # 可用工具
    tool_names = {
        "search_docs": "🔍 文档检索",
        "calculator": "🧮 计算器",
        "get_current_time": "🕐 当前时间",
        "read_file": "📖 读取文件",
        "list_files": "📂 列出文件",
        "python_repl": "🐍 Python沙箱",
        "write_file": "✍️ 写入文件",
    }
    with st.expander("🔧 可用工具"):
        for t in TOOL_DEFINITIONS:
            name = t["function"]["name"]
            st.caption(f"{tool_names.get(name, name)}")

    # 外观
    with st.expander("🎨 外观"):
        st.text_input("头像", max_chars=2, key="user_avatar")
        st.text_input("AI头像", max_chars=2, key="ai_avatar")
        st.session_state.color_name = st.selectbox("主题色", list(COLORS.keys()), key="color")
        st.session_state.accent_color = COLORS[st.session_state.color_name]

    # 统计
    stats = get_collection_stats(collection)
    with st.expander(f"📊 统计（{stats['document_count']}文档/{stats['chunk_count']}块）"):
        st.caption(f"模型: deepseek-chat")
        st.caption(f"向量维度: 384")

save_settings({k: st.session_state[k] for k in defaults})

# ============================================================
# CSS
# ============================================================
st.markdown(f"""<style>
    .stChatMessage {{ border-radius: 16px !important; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
    .stButton > button {{ border-color: {st.session_state.accent_color} !important; color: {st.session_state.accent_color} !important; border-radius: 8px !important; }}
    .stButton > button:hover {{ background-color: {st.session_state.accent_color} !important; color: white !important; }}
    button[kind="primary"] {{ background-color: {st.session_state.accent_color} !important; border-color: {st.session_state.accent_color} !important; color: white !important; }}
</style>""", unsafe_allow_html=True)

# ============================================================
# 主区域：聊天
# ============================================================
for msg in st.session_state.messages:
    avatar = st.session_state.user_avatar if msg["role"] == "user" else st.session_state.ai_avatar
    with st.chat_message(msg["role"], avatar=avatar):
        if msg.get("tool_steps"):
            for step in msg["tool_steps"]:
                emoji = TOOL_EMOJI.get(step["name"], "🔌")
                with st.expander(f"{emoji} {step['name']}"):
                    st.caption("📥 参数")
                    st.code(json.dumps(step["args"], ensure_ascii=False, indent=2), language="json")
                    st.caption("📤 结果")
                    st.text(step["result"][:800])
        st.markdown(msg["content"])

st.caption(f"📄 {stats['document_count']} 个文档已加载 | deepseek-chat | 温度 {st.session_state.temperature}")

# ============================================================
# 聊天输入
# ============================================================
if prompt := st.chat_input(
    "告诉我想对文档做什么：提取关键信息、总结要点、对比分析..."
    if stats["document_count"] > 0
    else "👈 先上传文档，我就能帮你处理"
):
    with st.chat_message("user", avatar=st.session_state.user_avatar):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant", avatar=st.session_state.ai_avatar):
        status_ph = st.empty()
        tool_ph = st.empty()
        answer_ph = st.empty()

        steps = []
        full_answer = ""

        try:
            for event in run_agent_streaming_answer(
                st.session_state.client, prompt, "deepseek-chat",
                st.session_state.temperature, st.session_state.max_iterations,
                st.session_state.api_messages.copy(),
            ):
                t = event["type"]

                if t == "tool_call":
                    emoji = TOOL_EMOJI.get(event["name"], "🔌")
                    status_ph.info(f"{emoji} {event['name']}...")
                    with tool_ph.container():
                        with st.expander(f"{emoji} {event['name']}", expanded=True):
                            st.code(json.dumps(event["args"], ensure_ascii=False, indent=2), language="json")

                elif t == "tool_result":
                    steps.append({"name": event["name"], "args": event.get("args", {}),
                                  "result": event["result"]})
                    with tool_ph.container():
                        for s in steps:
                            emoji = TOOL_EMOJI.get(s["name"], "🔌")
                            with st.expander(f"{emoji} {s['name']}", expanded=False):
                                st.caption("📥 参数")
                                st.code(json.dumps(s["args"], ensure_ascii=False, indent=2), language="json")
                                st.caption("📤 结果")
                                st.text(s["result"][:800])

                elif t == "text_chunk":
                    status_ph.empty()
                    full_answer += event["content"]
                    answer_ph.markdown(full_answer + "▌")

                elif t == "done":
                    status_ph.empty()
                    answer_ph.markdown(full_answer)

                elif t == "error":
                    status_ph.empty()
                    answer_ph.error(event["message"])
                    full_answer = f"❌ {event['message']}"

        except Exception as e:
            status_ph.empty()
            answer_ph.error(f"异常：{e}")
            full_answer = f"❌ {e}"

    st.session_state.messages.append({
        "role": "assistant", "content": full_answer, "tool_steps": steps,
    })
    st.session_state.api_messages.append({"role": "user", "content": prompt})
    st.session_state.api_messages.append({"role": "assistant", "content": full_answer})

    if steps:
        st.rerun()
