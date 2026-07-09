# 📚 RAG 文档问答

基于检索增强生成（RAG）的文档问答系统。上传文档后，AI 从中检索相关内容并回答。

## 功能

- 支持 7 种文档格式：PDF / TXT / MD / PY / JSON / CSV / LOG
- 文本智能切块 + 向量化 + ChromaDB 存储
- 语义检索：问题 → Embedding → 找最相关片段 → AI 回答
- 精确来源引用（文件名 + 片段号 + 相似度）
- 多文档跨文档检索

## 技术栈

```
Streamlit + DeepSeek API + ChromaDB + sentence-transformers + PyPDF2
```

## 运行

```bash
pip install -r requirements.txt
streamlit run app.py
```
