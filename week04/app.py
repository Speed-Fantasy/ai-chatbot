"""
Agent 聊天 — Streamlit 界面
AI 自主决策调用工具，展示思考和执行过程
"""
import os
import json
import streamlit as st
from openai import OpenAI
from agent_core import run_agent_streaming_answer
from tools import TOOL_DEFINITIONS

# ============================================================
# 路径 & 常量
# ============================================================
BASE_DIR = os.path.dirname(__file__)
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

COLORS = {
    "🟣 紫罗兰": "#6C63FF",
    "🔵 海洋蓝": "#1E90FF",
    "🟢 薄荷绿": "#00C9A7",
    "🟠 活力橙": "#FF6B35",
    "🔴 珊瑚红": "#FF6B6B",
    "🟡 琥珀金": "#F5A623",
}

TOOL_EMOJI = {
    "calculator": "🧮",
    "get_current_time": "🕐",
    "read_file": "📖",
    "list_files": "📂",
    "python_repl": "🐍",
    "write_file": "✍️",
}


# ============================================================
# 设置持久化
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
st.set_page_config(page_title="AI Agent", page_icon="🤖", layout="wide")
st.title("🤖 AI Agent")
st.caption("AI 自主决策 · 调用工具 · 完成任务")

# ============================================================
# 初始化会话状态
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_messages" not in st.session_state:
    st.session_state.api_messages = []  # API 级对话历史（不含 system prompt）

if "client" not in st.session_state:
    st.session_state.client = OpenAI(
        api_key=st.secrets["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )

defaults = {
    "temperature": 0.1,
    "max_iterations": 8,
    "user_avatar": "😎",
    "ai_avatar": "🤖",
    "user_name": "我",
    "ai_name": "Agent",
    "accent_color": "#6C63FF",
    "color_name": "🟣 紫罗兰",
}
saved = load_settings()
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = saved.get(key, val)

# ============================================================
# 侧边栏
# ============================================================
with st.sidebar:
    st.header("⚙️ Agent 设置")

    st.caption("模型：**deepseek-chat**（支持工具调用）")

    temperature = st.slider(
        "温度", 0.0, 1.5, st.session_state.temperature, 0.1,
        help="Agent 建议低温（0~0.3），保证稳定决策",
    )
    st.session_state.temperature = temperature

    st.session_state.max_iterations = st.slider(
        "最大循环次数", 3, 15, st.session_state.max_iterations, 1,
        help="防止 Agent 陷入无限循环",
    )

    st.divider()

    # 新对话按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ 新对话", use_container_width=True, type="primary"):
            st.session_state.messages = []
            st.session_state.api_messages = []
            st.rerun()
    with col2:
        st.caption(f"当前 {len(st.session_state.api_messages)//2} 轮对话")

    st.divider()
    st.header("🔧 可用工具")

    tool_names = {
        "calculator": "计算器",
        "get_current_time": "当前时间",
        "read_file": "读取文件",
        "list_files": "列出文件",
        "python_repl": "Python 沙箱",
        "write_file": "写入文件",
    }
    for tool in TOOL_DEFINITIONS:
        name = tool["function"]["name"]
        desc = tool["function"]["description"]
        emoji = TOOL_EMOJI.get(name, "🔌")
        with st.expander(f"{emoji} {tool_names.get(name, name)}"):
            st.caption(desc)

    st.divider()

    # 外观
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

    if st.button("🗑️ 清除对话", use_container_width=True):
        st.session_state.messages = []
        st.session_state.api_messages = []
        st.rerun()

    # 使用说明
    with st.expander("💡 试试这些"):
        st.markdown("""
        - 计算 (15*8+200)/4
        - 现在几点了？
        - 读一下 week04/tools.py
        - 列出当前目录的文件
        - 用 Python 算 1到100 的和
        - 先看看有哪些文件，再读其中一个
        """)

# 保存设置
save_settings({k: st.session_state[k] for k in defaults})

# ============================================================
# CSS
# ============================================================
css = f"""
<style>
    /* 聊天气泡 */
    .stChatMessage {{
        border-radius: 16px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: box-shadow 0.2s;
    }}
    .stChatMessage:hover {{
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
    }}

    /* 侧边栏标题 */
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] .stMarkdown h1 {{
        color: {st.session_state.accent_color} !important;
    }}

    /* 普通按钮 */
    .stButton > button {{
        border-color: {st.session_state.accent_color} !important;
        color: {st.session_state.accent_color} !important;
        border-radius: 8px !important;
    }}
    .stButton > button:hover {{
        background-color: {st.session_state.accent_color} !important;
        color: white !important;
    }}

    /* 主要按钮 */
    button[kind="primary"] {{
        background-color: {st.session_state.accent_color} !important;
        border-color: {st.session_state.accent_color} !important;
        color: white !important;
    }}

    /* 输入框焦点 */
    textarea:focus {{
        border-color: {st.session_state.accent_color} !important;
        box-shadow: 0 0 0 1px {st.session_state.accent_color} !important;
    }}

    /* 工具卡片 */
    .tool-card {{
        background: {st.session_state.accent_color}10;
        border-left: 4px solid {st.session_state.accent_color};
        border-radius: 8px;
        padding: 10px 14px;
        margin: 6px 0;
        font-size: 0.9em;
    }}
    .tool-card .tool-name {{
        color: {st.session_state.accent_color};
        font-weight: bold;
    }}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# ============================================================
# 主区域：聊天
# ============================================================

# 显示历史
for msg in st.session_state.messages:
    avatar = st.session_state.user_avatar if msg["role"] == "user" else st.session_state.ai_avatar
    with st.chat_message(msg["role"], avatar=avatar):
        # 显示工具调用过程
        if msg.get("tool_steps"):
            for step in msg["tool_steps"]:
                emoji = TOOL_EMOJI.get(step["name"], "🔌")
                with st.expander(f"{emoji} 调用工具：**{step['name']}**"):
                    st.caption("📥 参数")
                    st.code(json.dumps(step["args"], ensure_ascii=False, indent=2), language="json")
                    st.caption("📤 结果")
                    st.text(step["result"])

        # 显示回答
        st.markdown(msg["content"])

# 状态提示
st.caption(f"🤖 模型：deepseek-chat | 温度：{st.session_state.temperature} | 最多 {st.session_state.max_iterations} 轮")

# ============================================================
# 聊天输入
# ============================================================
if prompt := st.chat_input("给 Agent 一个任务..."):
    # 显示用户消息
    with st.chat_message("user", avatar=st.session_state.user_avatar):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 运行 Agent
    with st.chat_message("assistant", avatar=st.session_state.ai_avatar):
        # 占位区
        status_placeholder = st.empty()
        tool_placeholder = st.empty()
        answer_placeholder = st.empty()

        collected_steps = []  # 收集工具调用记录
        full_answer = ""

        # 启动 Agent 循环（传入历史，Agent 就能记住之前聊了什么）
        try:
            for event in run_agent_streaming_answer(
                client=st.session_state.client,
                user_task=prompt,
                model="deepseek-chat",
                temperature=st.session_state.temperature,
                max_iterations=st.session_state.max_iterations,
                history=st.session_state.api_messages.copy(),
            ):
                if event["type"] == "tool_call":
                    emoji = TOOL_EMOJI.get(event["name"], "🔌")
                    status_placeholder.info(f"{emoji} 正在调用：**{event['name']}**...")
                    # 在工具区显示当前调用
                    with tool_placeholder.container():
                        with st.expander(f"{emoji} 调用工具：**{event['name']}**", expanded=True):
                            st.caption("📥 参数")
                            st.code(json.dumps(event["args"], ensure_ascii=False, indent=2), language="json")

                elif event["type"] == "tool_result":
                    # 更新工具结果显示
                    collected_steps.append({
                        "name": event["name"],
                        "args": event.get("args", {}),
                        "result": event["result"],
                    })
                    with tool_placeholder.container():
                        for step in collected_steps:
                            emoji = TOOL_EMOJI.get(step["name"], "🔌")
                            with st.expander(f"{emoji} 调用工具：**{step['name']}**", expanded=False):
                                st.caption("📥 参数")
                                st.code(json.dumps(step["args"], ensure_ascii=False, indent=2), language="json")
                                st.caption("📤 结果")
                                st.text(step["result"])

                elif event["type"] == "text_chunk":
                    status_placeholder.empty()
                    full_answer += event["content"]
                    answer_placeholder.markdown(full_answer + "▌")

                elif event["type"] == "done":
                    status_placeholder.empty()
                    answer_placeholder.markdown(full_answer)

                elif event["type"] == "error":
                    status_placeholder.empty()
                    answer_placeholder.error(event["message"])
                    full_answer = f"❌ {event['message']}"

        except Exception as e:
            status_placeholder.empty()
            answer_placeholder.error(f"Agent 运行异常：{str(e)}")
            full_answer = f"❌ Agent 运行异常：{str(e)}"

    # 保存到显示历史
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_answer,
        "tool_steps": collected_steps,
    })

    # 保存到 API 对话历史（Agent 靠这个记住上下文）
    st.session_state.api_messages.append({"role": "user", "content": prompt})
    st.session_state.api_messages.append({"role": "assistant", "content": full_answer})

    # 如果 Agent 用了工具，最后刷新一下让工具卡片整齐显示
    if collected_steps:
        st.rerun()
