"""
AI 简历优化器 — Streamlit 应用
上传 → 分析 → JD匹配 → 改写 → 导出报告
"""
import os
import json
import streamlit as st
from openai import OpenAI
from resume_engine import extract_resume_text, analyze_resume, match_jd, rewrite_section

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(__file__)
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
DATA_FILE = os.path.join(BASE_DIR, "data.json")  # 简历数据持久化

COLORS = {
    "🟣 紫罗兰": "#6C63FF", "🔵 海洋蓝": "#1E90FF",
    "🟢 薄荷绿": "#00C9A7", "🟠 活力橙": "#FF6B35",
    "🔴 珊瑚红": "#FF6B6B", "🟡 琥珀金": "#F5A623",
}


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data():
    """把当前简历相关数据持久化到磁盘"""
    data = {
        "resume_text": st.session_state.resume_text,
        "resume_filename": st.session_state.resume_filename,
        "analysis_result": st.session_state.analysis_result,
        "jd_result": st.session_state.jd_result,
        "rewrite_results": st.session_state.rewrite_results,
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
# 页面
# ============================================================
st.set_page_config(page_title="AI 简历优化器", page_icon="📝", layout="wide")
st.title("📝 AI 简历优化器")
st.caption("上传简历 → AI 分析评分 → JD 匹配 → 智能改写 → 导出报告")

# ============================================================
# 会话状态
# ============================================================
if "client" not in st.session_state:
    st.session_state.client = OpenAI(
        api_key=st.secrets["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )
# 从磁盘恢复上次的简历数据（持久化）
saved_data = load_data()
if "resume_text" not in st.session_state:
    st.session_state.resume_text = saved_data.get("resume_text", "")
if "resume_filename" not in st.session_state:
    st.session_state.resume_filename = saved_data.get("resume_filename", "")
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = saved_data.get("analysis_result", "")
if "jd_result" not in st.session_state:
    st.session_state.jd_result = saved_data.get("jd_result", "")
if "rewrite_results" not in st.session_state:
    st.session_state.rewrite_results = saved_data.get("rewrite_results", [])

defaults = {
    "model": "deepseek-chat",
    "temperature": 0.3,
    "user_avatar": "😎", "ai_avatar": "🤖",
    "user_name": "我", "ai_name": "AI 助手",
    "accent_color": "#6C63FF", "color_name": "🟣 紫罗兰",
}
saved = load_settings()
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = saved.get(key, val)

# ============================================================
# 侧边栏
# ============================================================
with st.sidebar:
    st.header("⚙️ 设置")

    model = st.radio("模型", ["deepseek-chat", "deepseek-reasoner"],
                     index=0 if st.session_state.model == "deepseek-chat" else 1,
                     horizontal=True, key="model_radio")
    st.session_state.model = model
    temperature = None if model == "deepseek-reasoner" else st.slider(
        "温度", 0.0, 1.5, st.session_state.temperature, 0.1)
    st.session_state.temperature = temperature or 0.3

    st.divider()

    with st.expander("🎨 外观"):
        st.text_input("你的头像", max_chars=2, key="user_avatar")
        st.text_input("AI 头像", max_chars=2, key="ai_avatar")
        st.session_state.color_name = st.selectbox("主题色", list(COLORS.keys()), key="color_select")
        st.session_state.accent_color = COLORS[st.session_state.color_name]

    st.divider()
    st.subheader("📋 数据管理")
    st.caption(f"简历：{st.session_state.resume_filename or '未上传'}")
    st.caption(f"分析：{'✅' if st.session_state.analysis_result else '❌'}")
    st.caption(f"JD匹配：{'✅' if st.session_state.jd_result else '❌'}")
    st.caption(f"改写记录：{len(st.session_state.rewrite_results)} 条")

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🆕 清除全部", use_container_width=True):
            st.session_state.resume_text = ""
            st.session_state.resume_filename = ""
            st.session_state.analysis_result = ""
            st.session_state.jd_result = ""
            st.session_state.rewrite_results = []
            save_data()
            st.rerun()
    with col_b:
        if st.button("🗑️ 清除结果", use_container_width=True):
            st.session_state.analysis_result = ""
            st.session_state.jd_result = ""
            st.session_state.rewrite_results = []
            save_data()
            st.rerun()

save_settings({k: st.session_state[k] for k in defaults})

# ============================================================
# CSS
# ============================================================
st.markdown(f"""<style>
    .stButton > button {{ border-color: {st.session_state.accent_color} !important; color: {st.session_state.accent_color} !important; border-radius: 8px !important; }}
    .stButton > button:hover {{ background-color: {st.session_state.accent_color} !important; color: white !important; }}
    button[kind="primary"] {{ background-color: {st.session_state.accent_color} !important; border-color: {st.session_state.accent_color} !important; color: white !important; }}
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {{ color: {st.session_state.accent_color} !important; }}
    .stTabs [data-baseweb="tab"] {{ color: {st.session_state.accent_color} !important; }}
    .score-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-weight: bold; color: white; }}
    .score-high {{ background: #22c55e; }} .score-mid {{ background: #eab308; }} .score-low {{ background: #ef4444; }}
</style>""", unsafe_allow_html=True)

# ============================================================
# 主区域：6 个 Tab
# ============================================================
tabs = st.tabs(["📤 上传简历", "📊 AI 分析", "🎯 JD 匹配", "✍️ AI 改写", "📝 优化报告", "💡 使用说明"])

# ---- Tab 1: 上传简历 ----
with tabs[0]:
    st.subheader("上传你的简历")
    uploaded = st.file_uploader("支持 PDF / DOCX / TXT 格式", type=["pdf", "docx", "txt", "md"],
                                label_visibility="collapsed")

    if uploaded:
        with st.spinner("正在解析简历..."):
            text = extract_resume_text(uploaded, uploaded.name)

        if text.startswith("[解析失败]"):
            st.error(text)
        else:
            st.session_state.resume_text = text
            st.session_state.resume_filename = uploaded.name
            st.session_state.analysis_result = ""
            st.session_state.jd_result = ""
            st.session_state.rewrite_results = []

            st.success(f"✅ 解析成功！共 {len(text)} 字符")
            save_data()  # 持久化

            with st.expander("📄 预览简历内容"):
                st.text_area("简历文本", text, height=300, label_visibility="collapsed")

# ---- Tab 2: AI 分析 ----
with tabs[1]:
    st.subheader("AI 智能分析")

    if not st.session_state.resume_text:
        st.info("👈 请先在「上传简历」页面上传你的简历")
    else:
        if st.button("🔍 开始分析", type="primary", use_container_width=True):
            st.session_state.analysis_result = ""
            placeholder = st.empty()

            with st.spinner("AI 正在分析你的简历..."):
                for chunk, error in analyze_resume(
                    st.session_state.client, st.session_state.resume_text,
                    st.session_state.model, st.session_state.temperature
                ):
                    if error:
                        st.error(f"分析失败：{error}")
                        break
                    if chunk:
                        st.session_state.analysis_result += chunk
                        placeholder.markdown(st.session_state.analysis_result + "▌")
                placeholder.markdown(st.session_state.analysis_result)
                save_data()  # 持久化

        if st.session_state.analysis_result:
            st.divider()
            st.markdown(st.session_state.analysis_result)

# ---- Tab 3: JD 匹配 ----
with tabs[2]:
    st.subheader("JD 匹配对比")

    if not st.session_state.resume_text:
        st.info("👈 请先在「上传简历」页面上传你的简历")
    else:
        jd_text = st.text_area("粘贴目标岗位 JD（岗位描述）", height=200,
                               placeholder="将招聘网站上的岗位描述粘贴到这里...")

        if st.button("🎯 开始匹配", type="primary", use_container_width=True, disabled=not jd_text.strip()):
            st.session_state.jd_result = ""
            placeholder = st.empty()

            with st.spinner("AI 正在对比分析..."):
                for chunk, error in match_jd(
                    st.session_state.client, st.session_state.resume_text, jd_text,
                    st.session_state.model, st.session_state.temperature
                ):
                    if error:
                        st.error(f"匹配失败：{error}")
                        break
                    if chunk:
                        st.session_state.jd_result += chunk
                        placeholder.markdown(st.session_state.jd_result + "▌")
                placeholder.markdown(st.session_state.jd_result)
                save_data()  # 持久化

        if st.session_state.jd_result:
            st.divider()
            st.markdown(st.session_state.jd_result)

# ---- Tab 4: AI 改写 ----
with tabs[3]:
    st.subheader("AI 智能改写")

    if not st.session_state.resume_text:
        st.info("👈 请先在「上传简历」页面上传你的简历")
    else:
        col1, col2 = st.columns(2)
        with col1:
            original = st.text_area("粘贴要改写的原文",
                                    placeholder="例如：负责公司网站的维护和更新工作",
                                    height=120)
        with col2:
            requirement = st.text_area("改写要求（可选）",
                                       placeholder="例如：用STAR法则改写，突出量化成果\n或留空让AI自动优化",
                                       height=120)

        if st.button("✍️ 开始改写", type="primary", use_container_width=True, disabled=not original.strip()):
            req = requirement.strip() or "请用STAR法则改写，量化成果，使用强动词开头"

            placeholder = st.empty()
            full_reply = ""

            with st.spinner("AI 正在改写..."):
                for chunk, error in rewrite_section(
                    st.session_state.client, original, req,
                    st.session_state.model, st.session_state.temperature
                ):
                    if error:
                        st.error(f"改写失败：{error}")
                        break
                    if chunk:
                        full_reply += chunk
                        placeholder.markdown(full_reply + "▌")
                placeholder.markdown(full_reply)

            if full_reply:
                st.session_state.rewrite_results.append({
                    "original": original,
                    "requirement": req,
                    "rewritten": full_reply,
                })
                save_data()  # 持久化

        # 显示改写历史
        if st.session_state.rewrite_results:
            st.divider()
            st.subheader("📋 改写历史")
            for i, item in enumerate(reversed(st.session_state.rewrite_results)):
                with st.expander(f"改写 #{len(st.session_state.rewrite_results) - i}"):
                    st.caption("📄 原文")
                    st.text(item["original"])
                    st.caption("✨ 改写结果")
                    st.markdown(item["rewritten"])
                    if st.button("🗑️ 删除", key=f"del_rewrite_{i}"):
                        st.session_state.rewrite_results.pop(
                            len(st.session_state.rewrite_results) - 1 - i
                        )
                        save_data()
                        st.rerun()

# ---- Tab 5: 优化报告 ----
with tabs[4]:
    st.subheader("📝 综合优化报告")

    if not st.session_state.resume_text:
        st.info("👈 请先在「上传简历」页面上传你的简历")
    elif not st.session_state.analysis_result:
        st.info("👈 请先在「AI 分析」页面完成分析")
    else:
        # 组装报告
        report = f"""# 📝 AI 简历优化报告

> 简历：**{st.session_state.resume_filename}**
> 模型：{st.session_state.model}
> 温度：{st.session_state.temperature}

---

## 📊 AI 分析结果

{st.session_state.analysis_result}

---

## 🎯 JD 匹配结果

{st.session_state.jd_result or '（未进行 JD 匹配）'}

---

## ✍️ AI 改写记录

"""

        if st.session_state.rewrite_results:
            for i, item in enumerate(st.session_state.rewrite_results, 1):
                report += f"""
### 改写 #{i}

**原文：**
{item['original']}

**改写后：**
{item['rewritten']}

---
"""
        else:
            report += "\n（暂无改写记录）\n"

        st.markdown(report)

        # 下载按钮
        st.download_button(
            "📥 下载报告 (Markdown)",
            data=report,
            file_name=f"简历优化报告_{st.session_state.resume_filename}.md",
            mime="text/markdown",
            use_container_width=True,
        )

# ---- Tab 6: 使用说明 ----
with tabs[5]:
    st.subheader("💡 使用说明")

    st.markdown("""
    ### 📋 使用流程

    1. **上传简历** — 支持 PDF、DOCX、TXT 格式
    2. **AI 分析** — 从完整性、措辞、关键词、结构四个维度打分
    3. **JD 匹配**（可选）— 粘贴目标岗位，看匹配度
    4. **AI 改写** — 选中薄弱段落，AI 用 STAR 法则改写
    5. **导出报告** — 一键下载 Markdown 格式优化报告

    ### 🔑 核心功能

    | 功能 | 说明 |
    |------|------|
    | 四维评分 | 完整性、措辞力度、关键词、结构清晰度 |
    | JD 匹配 | 对比岗位要求，找出差距 |
    | STAR 改写 | 情境→任务→行动→结果，量化成果 |
    | 报告导出 | Markdown 格式，可直接打印 |

    ### 💡 提示

    - 分析建议低温（0.1-0.3），改写可适当提高（0.5-0.7）
    - deepseek-chat 用于日常分析和改写
    - deepseek-reasoner 适合深度分析复杂的简历结构问题
    - 可以多次改写同一段落，比较不同版本
    """)
