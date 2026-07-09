"""
RAG 智能文档问答 — Streamlit 应用
上传文档 → 自动向量化 → 提问 → AI 检索并回答（带来源引用）
"""
import os
import json
import streamlit as st
from openai import OpenAI

# 导入 RAG 核心管线
from rag_core import (
    init_embedding_model,
    init_chroma_client,
    reset_chroma_db,
    extract_text,
    chunk_document,
    index_chunks,
    retrieve,
    build_rag_prompt,
    get_document_list,
    get_collection_stats,
    delete_document,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_TOP_K,
    DEFAULT_MODEL_NAME,
)

# ============================================================
# 路径 & 常量
# ============================================================
BASE_DIR = os.path.dirname(__file__)
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
CHROMA_DB_PATH = os.path.join(BASE_DIR, "chroma_db")

SUPPORTED_TYPES = ["txt", "pdf", "md", "py", "json", "csv", "log"]
COLORS = {
    "🟣 紫罗兰": "#6C63FF",
    "🔵 海洋蓝": "#1E90FF",
    "🟢 薄荷绿": "#00C9A7",
    "🟠 活力橙": "#FF6B35",
    "🔴 珊瑚红": "#FF6B6B",
    "🟡 琥珀金": "#F5A623",
}


# ============================================================
# 设置持久化（复用 Week02 模式）
# ============================================================
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


# ============================================================
# 页面配置
# ============================================================
st.set_page_config(page_title="文档智能问答", page_icon="📚", layout="wide")
st.title("📚 智能文档问答")
st.caption("上传文档 → AI 理解 → 提问回答（带来源引用）")

# ============================================================
# 初始化会话状态
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "client" not in st.session_state:
    st.session_state.client = OpenAI(
        api_key=st.secrets["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )

if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()

# 加载用户设置
defaults = {
    "model": "deepseek-chat",
    "temperature": 0.7,
    "chunk_size": DEFAULT_CHUNK_SIZE,
    "chunk_overlap": DEFAULT_CHUNK_OVERLAP,
    "top_k": DEFAULT_TOP_K,
    "user_avatar": "😎",
    "ai_avatar": "🤖",
    "user_name": "我",
    "ai_name": "AI 助手",
    "accent_color": "#6C63FF",
    "color_name": "🟣 紫罗兰",
}
saved = load_settings()
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = saved.get(key, val)

# ============================================================
# 初始化 RAG 组件（缓存，避免反复加载）
# ============================================================
@st.cache_resource
def get_embedding_model():
    """加载嵌入模型（只下载一次，之后走缓存）"""
    return init_embedding_model(DEFAULT_MODEL_NAME)


@st.cache_resource
def get_chroma():
    """初始化 ChromaDB（持久化到磁盘）"""
    client, collection = init_chroma_client(CHROMA_DB_PATH)
    return client, collection


embedding_model = get_embedding_model()
chroma_client, collection = get_chroma()

# ============================================================
# 侧边栏
# ============================================================
with st.sidebar:
    st.header("⚙️ 设置")

    # --- 模型选择 ---
    st.session_state.model = st.selectbox(
        "模型",
        ["deepseek-chat", "deepseek-reasoner"],
        index=0 if st.session_state.model == "deepseek-chat" else 1,
        key="model_select",
    )
    # reasoner 不支持 temperature
    if st.session_state.model == "deepseek-reasoner":
        temperature = None
    else:
        temperature = st.slider("温度", 0.0, 2.0, st.session_state.temperature, 0.1, key="temp_slider")
        st.session_state.temperature = temperature

    st.divider()
    st.header("📁 文档管理")

    # --- 切块参数 ---
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.chunk_size = st.number_input(
            "分块大小", min_value=50, max_value=4000, value=st.session_state.chunk_size, step=50,
            help="每个文本块的字符数，越小越精细",
        )
    with col2:
        st.session_state.chunk_overlap = st.number_input(
            "重叠大小", min_value=0, max_value=500, value=st.session_state.chunk_overlap, step=10,
            help="相邻块之间重叠的字符数",
        )
    # 防止重叠 > 块大小的一半
    if st.session_state.chunk_overlap > st.session_state.chunk_size // 2:
        st.session_state.chunk_overlap = st.session_state.chunk_size // 2

    st.session_state.top_k = st.number_input(
        "Top-K 检索", min_value=1, max_value=20, value=st.session_state.top_k, step=1,
        help="每次检索返回的最相关片段数",
    )

    st.divider()

    # --- 文件上传 ---
    uploaded_files = st.file_uploader(
        "上传文档（支持 txt, pdf, md, py, json, csv, log）",
        type=SUPPORTED_TYPES,
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    # --- 处理上传文件 ---
    if uploaded_files:
        for uploaded_file in uploaded_files:
            filename = uploaded_file.name

            # 跳过已处理的文件
            if filename in st.session_state.processed_files:
                continue

            # 读文件内容
            text = extract_text(uploaded_file, filename)

            # 空文件跳过
            if not text or not text.strip():
                st.warning(f"⚠️ **{filename}** 内容为空，已跳过")
                continue

            # 切块
            with st.spinner(f"🔍 正在分析「{filename}」..."):
                chunks = chunk_document(
                    text, filename,
                    chunk_size=st.session_state.chunk_size,
                    chunk_overlap=st.session_state.chunk_overlap,
                )

            # 大文件警告
            if len(chunks) > 500:
                st.warning(f"📦 **{filename}** 较大，生成 {len(chunks)} 个块，请耐心等待...")

            # 向量化 + 存储
            with st.spinner(f"🧠 正在向量化「{filename}」({len(chunks)} 个片段)..."):
                count = index_chunks(chunks, collection, embedding_model)

            st.session_state.processed_files.add(filename)
            st.toast(f"✅ **{filename}** 已加载（{count} 个片段）", icon="✅")

    # --- 已加载文档列表 ---
    doc_list = get_document_list(collection)
    if doc_list:
        st.caption(f"已加载文档（{len(doc_list)} 个）")

        for doc in doc_list:
            col_name, col_btn = st.columns([4, 1])
            with col_name:
                st.text(f"📄 {doc}")
            with col_btn:
                if st.button("✕", key=f"del_{doc}", help=f"删除 {doc}"):
                    delete_document(doc, collection)
                    if doc in st.session_state.processed_files:
                        st.session_state.processed_files.discard(doc)
                    st.toast(f"🗑️ **{doc}** 已删除")
                    st.rerun()

        st.divider()
        if st.button("🗑️ 清除所有文档", use_container_width=True):
            chroma_client, collection = reset_chroma_db(CHROMA_DB_PATH)
            st.session_state.processed_files = set()
            st.session_state.messages = []
            st.toast("已清除所有文档")
            st.rerun()

    st.divider()

    # --- 统计信息 ---
    stats = get_collection_stats(collection)
    st.header("📊 统计信息")
    st.metric("文档数量", stats["document_count"])
    st.metric("总片段数", stats["chunk_count"])
    st.caption(f"向量维度: 384 | 模型: paraphrase-multilingual-MiniLM-L12-v2")

    st.divider()

    # --- 外观设置 ---
    with st.expander("🎨 外观设置"):
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("你的头像", max_chars=2, key="user_avatar")
            st.text_input("你的昵称", max_chars=10, key="user_name")
        with col2:
            st.text_input("AI 头像", max_chars=2, key="ai_avatar")
            st.text_input("AI 昵称", max_chars=10, key="ai_name")
        st.session_state.color_name = st.selectbox("主题色", list(COLORS.keys()), key="color_select")
        st.session_state.accent_color = COLORS[st.session_state.color_name]

    st.divider()

    # --- 使用说明 ---
    with st.expander("💡 使用说明"):
        st.markdown("""
        1. **上传文档** — 支持 txt, pdf, md, py, json, csv
        2. **等待向量化** — 文档会自动切块并生成向量索引
        3. **在聊天框提问** — AI 会自动检索相关片段并回答
        4. **展开来源引用** — 每条回答下方可查看引用来源

        **提示：** 上传的文档越多，能回答的问题范围越大！
        """)

# 保存设置
save_settings({k: st.session_state[k] for k in defaults})

# ============================================================
# 动态 CSS
# ============================================================
css = f"""
<style>
    /* 聊天气泡圆角 + 阴影 */
    .stChatMessage {{
        border-radius: 16px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: box-shadow 0.2s;
    }}
    .stChatMessage:hover {{
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
    }}
    /* 侧边栏标题颜色 */
    .stSidebar h1, .stSidebar h2, .stSidebar h3 {{
        color: {st.session_state.accent_color} !important;
    }}
    /* 按钮主题色 */
    .stButton > button {{
        border-color: {st.session_state.accent_color} !important;
        color: {st.session_state.accent_color} !important;
    }}
    .stButton > button:hover {{
        background-color: {st.session_state.accent_color} !important;
        color: white !important;
    }}
    /* 来源引用卡片 */
    .source-card {{
        background: {st.session_state.accent_color}15;
        border-left: 4px solid {st.session_state.accent_color};
        border-radius: 8px;
        padding: 10px 14px;
        margin: 6px 0;
        font-size: 0.9em;
    }}
    .source-card .score-high   {{ color: #22c55e; font-weight: bold; }}
    .source-card .score-medium {{ color: #eab308; font-weight: bold; }}
    .source-card .score-low    {{ color: #ef4444; font-weight: bold; }}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# ============================================================
# 主区域：聊天界面
# ============================================================

# 显示历史消息
for msg in st.session_state.messages:
    avatar = st.session_state.user_avatar if msg["role"] == "user" else st.session_state.ai_avatar
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        # 如果有来源引用，显示在可展开区域
        if msg.get("sources"):
            with st.expander("📎 参考来源（点击展开）"):
                for i, src in enumerate(msg["sources"], 1):
                    score = src["score"]
                    if score >= 0.8:
                        score_class = "score-high"
                    elif score >= 0.6:
                        score_class = "score-medium"
                    else:
                        score_class = "score-low"
                    st.markdown(
                        f"""<div class="source-card">
                        <strong>[{i}] {src['source']}</strong> — 片段 #{src['chunk_index']}
                        &nbsp; 相似度: <span class="{score_class}">{score}</span>
                        <br><small>{src['text'][:300]}{'...' if len(src['text']) > 300 else ''}</small>
                        </div>""",
                        unsafe_allow_html=True,
                    )

# 当前模型提示
if st.session_state.model == "deepseek-reasoner":
    st.caption(f"🧠 当前模型：**deepseek-reasoner**（深度推理模式）| 已加载 {stats['document_count']} 个文档")
else:
    st.caption(f"💬 当前模型：**deepseek-chat** | 温度：{st.session_state.temperature} | 已加载 {stats['document_count']} 个文档")

# ============================================================
# 聊天输入
# ============================================================
if prompt := st.chat_input(
    "输入你的问题..."
    if stats["document_count"] > 0
    else "请先在侧边栏上传文档..."
):
    # 先显示用户消息
    with st.chat_message("user", avatar=st.session_state.user_avatar):
        st.markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})

    # 检查是否有文档
    if stats["document_count"] == 0:
        with st.chat_message("assistant", avatar=st.session_state.ai_avatar):
            st.info("📄 请先在侧边栏上传至少一个文档，然后我就能回答相关问题了！")
        st.session_state.messages.append({
            "role": "assistant",
            "content": "📄 请先在侧边栏上传至少一个文档，然后我就能回答相关问题了！",
        })
    else:
        # === RAG 核心流程 ===
        # 1. 检索相关片段
        with st.spinner("🔍 正在检索相关文档片段..."):
            retrieved_chunks = retrieve(
                prompt, collection, embedding_model, st.session_state.top_k
            )

        # 2. 拼装 Prompt
        rag_prompt = build_rag_prompt(prompt, retrieved_chunks)

        # 3. 调用 DeepSeek 流式生成
        with st.chat_message("assistant", avatar=st.session_state.ai_avatar):
            reply_placeholder = st.empty()
            thinking_placeholder = st.empty()
            full_reply = ""
            reasoning_content = ""

            try:
                kwargs = {
                    "model": st.session_state.model,
                    "messages": [{"role": "user", "content": rag_prompt}],
                    "stream": True,
                }
                if temperature is not None:
                    kwargs["temperature"] = temperature

                stream = st.session_state.client.chat.completions.create(**kwargs)

                for chunk in stream:
                    delta = chunk.choices[0].delta

                    # reasoner 思考过程
                    if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                        reasoning_content += delta.reasoning_content
                        with thinking_placeholder.expander("💭 思考中..."):
                            st.markdown(reasoning_content)

                    # 正文
                    if delta.content:
                        full_reply += delta.content
                        reply_placeholder.markdown(full_reply + "▌")

                reply_placeholder.markdown(full_reply)

                # 显示来源引用
                if retrieved_chunks:
                    with st.expander("📎 参考来源（点击展开）"):
                        for i, src in enumerate(retrieved_chunks, 1):
                            score = src["score"]
                            if score >= 0.8:
                                score_class = "score-high"
                            elif score >= 0.6:
                                score_class = "score-medium"
                            else:
                                score_class = "score-low"
                            st.markdown(
                                f"""<div class="source-card">
                                <strong>[{i}] {src['source']}</strong> — 片段 #{src['chunk_index']}
                                &nbsp; 相似度: <span class="{score_class}">{score}</span>
                                <br><small>{src['text'][:300]}{'...' if len(src['text']) > 300 else ''}</small>
                                </div>""",
                                unsafe_allow_html=True,
                            )

            except Exception as e:
                error_msg = str(e)
                if "rate" in error_msg.lower() or "429" in error_msg:
                    reply_placeholder.error("API 请求过于频繁，请稍后再试。")
                elif "auth" in error_msg.lower() or "401" in error_msg or "403" in error_msg:
                    reply_placeholder.error("API Key 无效，请检查 .streamlit/secrets.toml 配置。")
                else:
                    reply_placeholder.error(f"API 错误：{error_msg}")
                full_reply = f"[错误] {error_msg}"
                retrieved_chunks = []

        # 保存到聊天历史
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_reply,
            "sources": retrieved_chunks,
        })
