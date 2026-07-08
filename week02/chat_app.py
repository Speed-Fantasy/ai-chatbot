import streamlit as st
from openai import OpenAI
import json
import os

# ===== 🎨 个性化：从本地文件加载设置（刷新不丢失）=====
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

# 页面设置
st.set_page_config(page_title="AI 聊天助手", page_icon="🤖")
st.title("🤖 AI 聊天助手")

# 初始化
if "messages" not in st.session_state:
    st.session_state.messages = []

if "client" not in st.session_state:
    # 🎨 本地读 secrets.toml，云端读 Streamlit Cloud Secrets
    st.session_state.client = OpenAI(
        api_key=st.secrets["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )

# ===== 🎨 个性化：外观默认值（优先读本地文件）=====
defaults = {
    "user_avatar": "😎",
    "ai_avatar": "🤖",
    "user_name": "我",
    "ai_name": "AI 助手",
    "accent_color": "#6C63FF",
    "color_name": "🟣 紫罗兰",  # 主题色名称，和 selectbox 对应
}
saved = load_settings()
for key, default in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = saved.get(key, default)

# 每次设置变动时自动保存（包含 color_name 才能正确恢复）
save_settings({k: st.session_state[k] for k in defaults})

# ===== 侧边栏：放最前面，这样后面代码能用 model 和 temperature =====
with st.sidebar:
    st.header("⚙️ 设置")

    # 选模型（存到 session_state 确保切换生效）
    st.session_state.model = st.selectbox(
        "模型",
        ["deepseek-chat", "deepseek-reasoner"],
        index=0 if st.session_state.get("model") != "deepseek-reasoner" else 1,
        help="chat=日常对话，reasoner=深度推理",
    )

    # reasoner 不支持调温度，只有 chat 才能调
    if st.session_state.model == "deepseek-chat":
        temperature = st.slider(
            "温度",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1,
            help="越高越有创意，越低越严谨",
        )
    else:
        temperature = None

    st.divider()
    # ===== 🎨 个性化：外观设置 =====
    st.header("🎨 外观")

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("你的头像", max_chars=2, key="user_avatar")       # 🎨 key 绑定 session_state
    with col2:
        st.text_input("AI 头像", max_chars=2, key="ai_avatar")         # 🎨 key 绑定 session_state

    st.text_input("你的昵称", max_chars=10, key="user_name")            # 🎨 key 绑定 session_state
    st.text_input("AI 昵称", max_chars=10, key="ai_name")              # 🎨 key 绑定 session_state

    preset_colors = {
        "🟣 紫罗兰": "#6C63FF",
        "🔵 海洋蓝": "#1E90FF",
        "🟢 薄荷绿": "#00C9A7",
        "🟠 活力橙": "#FF6B35",
        "🔴 珊瑚红": "#FF6B6B",
        "🟡 琥珀金": "#F5A623",
    }
    color_name = st.selectbox("主题色", list(preset_colors.keys()), key="color_name")                 # 🎨 key 绑定
    st.session_state.accent_color = preset_colors[color_name]

    st.divider()
    st.subheader("📎 文件上传")

    uploaded_file = st.file_uploader(
        "上传文件让 AI 总结",
        type=["txt", "py", "md", "json", "csv", "log"],
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        # 读文件内容
        file_content = uploaded_file.read().decode("utf-8", errors="ignore")

        # 限制长度，防止超出 token 限制
        if len(file_content) > 8000:
            file_content = file_content[:8000] + "\n...(内容过长，已截断)"

        # 显示文件预览
        with st.expander(f"📄 {uploaded_file.name}（{len(file_content)} 字）"):
            st.code(file_content[:2000], language="text")

        if st.button("🔍 AI 总结文件", use_container_width=True):
            summary_prompt = f"""请总结以下文件的内容。用简洁的中文回答，包含：
            1. 文件类型和用途
            2. 核心内容要点（3-5条）
            3. 值得注意的细节

            文件内容：
            {file_content}"""

            # 把总结请求发给 AI（不影响正常对话历史）
            summary_messages = st.session_state.messages.copy()
            summary_messages.append({"role": "user", "content": summary_prompt})

            kwargs = {"model": st.session_state.model, "messages": summary_messages, "stream": True}
            if temperature is not None:
                kwargs["temperature"] = temperature

            stream = st.session_state.client.chat.completions.create(**kwargs)

            # 显示在聊天区
            with st.chat_message("assistant", avatar=st.session_state.ai_avatar):  # 🎨 个性头像
                reply_placeholder = st.empty()
                full_reply = ""

                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_reply += chunk.choices[0].delta.content
                        reply_placeholder.markdown(full_reply + "▌")

                reply_placeholder.markdown(full_reply)

            # 保存到对话历史
            st.session_state.messages.append(
                {"role": "user", "content": f"请总结我上传的文件「{uploaded_file.name}」"}
            )
            st.session_state.messages.append({"role": "assistant", "content": full_reply})
            st.rerun()

    st.divider()

    if st.button("🗑️ 清除对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ===== 🎨 个性化：动态 CSS（放在侧边栏后面，确保拿到最新的主题色）=====
accent = st.session_state.accent_color
st.markdown(f"""
<style>
    [data-testid="stChatMessage"] {{
        border-radius: 16px !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        margin-bottom: 12px;
        padding: 10px 16px !important;
    }}
    [data-testid="stChatMessage"]:hover {{
        box-shadow: 0 4px 20px rgba(0,0,0,0.10);
    }}
    /* 🎨 主题色应用 */
    section[data-testid="stSidebar"] h2 {{
        color: {accent} !important;
    }}
    [data-testid="stChatInput"] textarea {{
        border-color: {accent} !important;
    }}
    .stButton > button {{
        border-color: {accent} !important;
        color: {accent} !important;
    }}
    .stButton > button:hover {{
        background-color: {accent}22 !important;
    }}
</style>
""", unsafe_allow_html=True)

# ===== 主页面：消息显示 + 输入框 =====

# ===== 🎨 个性化：显示历史消息（用自定义头像+昵称）=====
for msg in st.session_state.messages:
    avatar = st.session_state.user_avatar if msg["role"] == "user" else st.session_state.ai_avatar
    name = st.session_state.user_name if msg["role"] == "user" else st.session_state.ai_name
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])

# 显示当前模型
st.caption(f"当前模型：{st.session_state.model}")

# 用户输入
if user_input := st.chat_input("输入消息..."):
    with st.chat_message("user", avatar=st.session_state.user_avatar):  # 🎨 个性头像
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 调 AI
    kwargs = {"model": st.session_state.model, "messages": st.session_state.messages, "stream": True}
    if temperature is not None:
        kwargs["temperature"] = temperature

    stream = st.session_state.client.chat.completions.create(**kwargs)

    # 手动读流，适配两种模型
    with st.chat_message("assistant", avatar=st.session_state.ai_avatar):  # 🎨 个性头像
        # reasoner 先显示思考过程
        if st.session_state.model == "deepseek-reasoner":
            thinking_placeholder = st.empty()

        reply_placeholder = st.empty()
        full_reply = ""
        thinking = ""

        for chunk in stream:
            delta = chunk.choices[0].delta

            # reasoner 的思考过程
            if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                thinking += delta.reasoning_content
                if st.session_state.model == "deepseek-reasoner":
                    with thinking_placeholder.expander("💭 思考中..."):
                        st.write(thinking)

            # 正式回复
            if delta.content:
                full_reply += delta.content
                reply_placeholder.markdown(full_reply + "▌")

        reply_placeholder.markdown(full_reply)

    st.session_state.messages.append({"role": "assistant", "content": full_reply})
