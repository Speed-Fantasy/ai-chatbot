"""
简历解析 + AI 分析引擎
"""
import io
import json
from PyPDF2 import PdfReader


def extract_resume_text(file_bytes, filename: str) -> str:
    """解析简历文件，返回纯文本"""
    ext = filename.lower().split(".")[-1] if "." in filename else ""

    try:
        if ext == "pdf":
            reader = PdfReader(io.BytesIO(file_bytes.read()))
            return "\n".join(
                page.extract_text() or "" for page in reader.pages
            )
        elif ext == "docx":
            import docx
            doc = docx.Document(io.BytesIO(file_bytes.read()))
            return "\n".join(p.text for p in doc.paragraphs)
        else:  # txt, md, etc.
            raw = file_bytes.read()
            for enc in ["utf-8", "gbk", "latin-1"]:
                try:
                    return raw.decode(enc)
                except (UnicodeDecodeError, LookupError):
                    continue
            return raw.decode("utf-8", errors="ignore")
    except Exception as e:
        return f"[解析失败] {filename}: {str(e)}"


def analyze_resume(client, resume_text: str, model: str = "deepseek-chat", temperature: float = 0.3):
    """
    AI 全面分析简历，返回结构化结果（流式）
    """
    prompt = f"""你是一位资深 HR 和简历优化专家。请仔细分析以下简历，给出专业的评估报告。

## 评估维度（每项0-100分）

1. **完整性** — 是否包含所有关键板块（个人信息、求职意向、教育背景、实习/工作经历、项目经历、技能、证书等）
2. **措辞力度** — 是否使用主动语态、量化成果（数字、百分比）、STAR法则
3. **关键词** — 是否包含行业热门关键词（AI/数据分析/项目管理等）
4. **结构清晰度** — 排版逻辑是否清晰、层次是否分明
5. **综合评分** — 整体竞争力

## 输出格式

请用以下格式输出（Markdown）：

### 📊 评分总览
| 维度 | 评分 | 说明 |
|------|------|------|
| 完整性 | XX/100 | ... |
| 措辞力度 | XX/100 | ... |
| 关键词 | XX/100 | ... |
| 结构清晰度 | XX/100 | ... |
| **综合评分** | **XX/100** | ... |

### 🔴 主要问题（列出3-5条最关键的问题，按严重程度排序）
1. ...
2. ...

### 💡 优化建议（按优先级排序）
1. ...
2. ...

### ✅ 亮点（做得好的地方，继续保持）
- ...

---

简历内容：

{resume_text}"""

    return _stream_api(client, model, prompt, temperature)


def match_jd(client, resume_text: str, jd_text: str, model: str = "deepseek-chat", temperature: float = 0.3):
    """
    JD 与简历匹配分析（流式）
    """
    prompt = f"""你是一位招聘专家。请对比以下简历和岗位描述(JD)，给出匹配分析。

## 输出格式

### 🎯 匹配度总评
- **综合匹配度**：XX%（估算）
- **是否建议投递**：是/谨慎/否

### ✅ 匹配的技能和经验
| 你的技能/经验 | JD要求 | 匹配说明 |
|--------------|--------|----------|
| ... | ... | ... |

### ❌ 缺失的技能和经验
| JD要求 | 重要程度 | 建议 |
|--------|----------|------|
| ... | 高/中/低 | 如何弥补... |

### 📝 简历调整建议
1. **必须修改**：...
2. **建议添加**：...
3. **可以弱化**：...

---

## 简历内容
{resume_text}

## 岗位描述(JD)
{jd_text}"""

    return _stream_api(client, model, prompt, temperature)


def rewrite_section(client, original_text: str, requirement: str, model: str = "deepseek-chat", temperature: float = 0.5):
    """
    AI 改写简历片段（流式）
    """
    prompt = f"""你是一位专业的简历写手。请根据要求改写以下简历片段。

## 改写原则
- 使用 STAR 法则（情境→任务→行动→结果）
- 量化成果（数字、百分比、具体数据）
- 主动语态，强动词开头
- 简洁有力，每条不超过2行
- 保持原意，不虚构经历

## 改写要求
{requirement}

## 原文
{original_text}

请输出改写后的版本，并简要说明改了什么。"""

    return _stream_api(client, model, prompt, temperature)


def _stream_api(client, model: str, prompt: str, temperature: float):
    """流式调用 API，yield 文本块"""
    try:
        kwargs = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        if temperature is not None:
            kwargs["temperature"] = temperature

        stream = client.chat.completions.create(**kwargs)

        full_text = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                full_text += token
                yield token, None  # (chunk_text, error)

        yield full_text, None  # final: full text

    except Exception as e:
        yield "", str(e)
