# AI 应用开发学习项目

2026年暑期两个月（7-8月）AI 应用开发速成，从零到能做完整产品。

## 项目总览

| 周次 | 项目 | 技术栈 | 核心能力 |
|------|------|--------|----------|
| Week 1 | CLI 聊天机器人 | Python + DeepSeek API | API 调用、流式输出、多轮对话 |
| Week 2 | Streamlit 聊天网页 | Streamlit + DeepSeek | Web UI、文件上传、个性化 |
| Week 3 | RAG 文档问答 | ChromaDB + Embedding | 向量数据库、语义检索、文档切片 |
| Week 4 | AI Agent | Tool Calling + Agent Loop | 工具调用、自主决策、多步执行 |
| Week 5 | AI 简历优化器 | Streamlit + DeepSeek | 完整产品、多模块、持久化 |
| Week 6 | 文档处理 Agent | RAG + Agent + ChromaDB | 文档检索、自主工具调用、综合处理 |

## 技术栈

```
Python / Streamlit / DeepSeek API / ChromaDB / sentence-transformers / PyPDF2 / python-docx
```

## 运行

每个项目独立运行：

```bash
pip install -r weekXX/requirements.txt
streamlit run weekXX/app.py
```

Week 1 为命令行程序：

```bash
python week01/chatbot_stream.py
```

## 学习路径

```
调用 API 层 → 工作流编排层 → RAG 层 → Agent 层 → 完整产品
```

## 作者

Klk — 山西农业大学 计算机科学与技术 2024级
