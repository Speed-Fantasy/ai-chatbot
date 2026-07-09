# 📄 文档处理 Agent

RAG + Agent 合体项目。上传文档后，Agent 自主决定用什么工具来处理——检索、分析、提取、改写、保存结果。

## 功能

- 上传任意文档（PDF/DOCX/TXT/MD/PY/JSON/CSV）
- Agent 自主在文档中**语义搜索**
- 多文档**交叉对比分析**
- 分析结果**自动保存**为文件
- 支持计算、Python 数据处理、文件管理等 7 个工具
- 对话历史持久化，刷新不丢失

## 技术栈

```
Streamlit + DeepSeek API + ChromaDB + sentence-transformers + Agent Loop
```

## 运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 截图

<!-- TODO: 替换为实际截图 -->
![screenshot](screenshot.png)

## 架构

```
用户提问 → Agent决策 → search_docs(ChromaDB) / read_file / python_repl / ...
                    → 看结果 → 再决策 → ... → 流式回答
```
