"""
RAG 核心管线：文档处理 → 文本切块 → 向量化 → 存储 → 检索
底层实现，不依赖 Streamlit，可以单独 import 使用
"""
import os
import re
import json
from io import BytesIO

# 国内用户：用 HF 镜像下载模型，避免被墙
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader

# ============================================================
# 配置
# ============================================================

# 默认嵌入模型：支持中英文的多语言模型
DEFAULT_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
# 如果更偏重中文，可以换用 BAAI/bge-small-zh-v1.5（取消下一行注释）
# DEFAULT_MODEL_NAME = "BAAI/bge-small-zh-v1.5"

# ChromaDB 集合名称
COLLECTION_NAME = "rag_docs_week03"

# 默认切块参数
DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 100
DEFAULT_TOP_K = 4

# 预定义分隔符（含中文标点，保证中文文本也能合理切分）
CHINESE_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]

# ============================================================
# 嵌入模型
# ============================================================

_embedding_model = None  # 模块级单例，避免反复加载


def init_embedding_model(model_name: str = DEFAULT_MODEL_NAME) -> SentenceTransformer:
    """加载本地 Embedding 模型（单例，只加载一次）"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(model_name)
    return _embedding_model


# ============================================================
# ChromaDB 客户端
# ============================================================

def init_chroma_client(persist_path: str) -> tuple:
    """
    初始化 ChromaDB 持久化客户端，返回 (client, collection)
    persist_path: 数据库存储目录，如 "week03/chroma_db"
    """
    os.makedirs(persist_path, exist_ok=True)

    client = chromadb.PersistentClient(
        path=persist_path,
        settings=ChromaSettings(anonymized_telemetry=False),
    )

    # 获取或创建集合（用余弦距离）
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    return client, collection


def reset_chroma_db(persist_path: str):
    """重置向量数据库（删除所有文档）"""
    import shutil
    if os.path.exists(persist_path):
        shutil.rmtree(persist_path)
    # 重新初始化
    return init_chroma_client(persist_path)


# ============================================================
# 文本提取
# ============================================================

def extract_text(file_bytes: BytesIO, filename: str) -> str:
    """
    根据文件类型提取文本内容
    返回提取到的文本字符串，失败返回空字符串
    """
    ext = os.path.splitext(filename)[1].lower()

    try:
        if ext == ".pdf":
            return _extract_from_pdf(file_bytes)
        elif ext == ".csv":
            return _extract_from_csv(file_bytes)
        elif ext == ".json":
            return _extract_from_json(file_bytes)
        else:
            # txt, md, py, log 等纯文本文件
            return _extract_from_text(file_bytes)
    except Exception as e:
        # 所有异常都不应该让程序崩溃
        print(f"[extract_text] 提取文件 '{filename}' 失败: {e}")
        return ""


def _extract_from_pdf(file_bytes: BytesIO) -> str:
    """从 PDF 提取文本"""
    reader = PdfReader(file_bytes)
    texts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            texts.append(page_text)
    return "\n\n".join(texts)


def _extract_from_csv(file_bytes: BytesIO) -> str:
    """从 CSV 提取文本（pandas 读取后转字符串）"""
    import pandas as pd
    df = pd.read_csv(BytesIO(file_bytes.read()))
    # 用 tabulate 风格的纯文本表示
    return df.to_string(index=False)


def _extract_from_json(file_bytes: BytesIO) -> str:
    """从 JSON 提取文本（格式化输出）"""
    data = json.loads(file_bytes.read().decode("utf-8"))
    return json.dumps(data, ensure_ascii=False, indent=2)


def _extract_from_text(file_bytes: BytesIO) -> str:
    """从纯文本文件提取，编码自动降级"""
    raw = file_bytes.read()
    # 尝试 UTF-8 → GBK → latin-1 降级
    for encoding in ["utf-8", "gbk", "latin-1"]:
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    # 最终兜底
    return raw.decode("utf-8", errors="ignore")


# ============================================================
# 文本切块
# ============================================================

def chunk_document(
    text: str,
    source: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[dict]:
    """
    把长文本切分成多个块，返回 [{"text": ..., "source": ..., "chunk_index": ...}, ...]
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=CHINESE_SEPARATORS,
        keep_separator=True,
    )

    chunks = splitter.split_text(text)

    return [
        {
            "text": chunk,
            "source": source,
            "chunk_index": i,
        }
        for i, chunk in enumerate(chunks)
    ]


# ============================================================
# 向量化 + 存储
# ============================================================

def index_chunks(
    chunks: list[dict],
    collection,
    model: SentenceTransformer,
) -> int:
    """
    批量向量化并写入 ChromaDB
    返回写入的块数量
    """
    if not chunks:
        return 0

    texts = [c["text"] for c in chunks]
    metadatas = [{"source": c["source"], "chunk_index": c["chunk_index"]} for c in chunks]
    ids = [_make_chunk_id(c["source"], c["chunk_index"]) for c in chunks]

    # 批量向量化（显示进度条）
    embeddings = model.encode(texts, show_progress_bar=False).tolist()

    # 写入 ChromaDB
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    return len(chunks)


# ============================================================
# 检索
# ============================================================

def retrieve(
    question: str,
    collection,
    model: SentenceTransformer,
    top_k: int = DEFAULT_TOP_K,
) -> list[dict]:
    """
    语义检索：把问题向量化，在 ChromaDB 中找最相似的 top_k 个块
    返回 [{"text": ..., "source": ..., "chunk_index": ..., "score": ...}, ...]
    """
    if collection.count() == 0:
        return []

    question_embedding = model.encode(question).tolist()

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=min(top_k, collection.count()),
    )

    # 把 ChromaDB 返回结果转成易用的字典列表
    chunks = []
    if results["ids"] and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            doc_text = results["documents"][0][i] if results["documents"][0] else ""
            meta = results["metadatas"][0][i] if results["metadatas"][0] else {}
            distance = results["distances"][0][i] if results["distances"][0] else 0
            # ChromaDB 用余弦距离，相似度 = 1 - 距离
            similarity = round(1 - distance, 4)

            chunks.append({
                "text": doc_text,
                "source": meta.get("source", "未知"),
                "chunk_index": meta.get("chunk_index", 0),
                "score": similarity,
            })

    return chunks


# ============================================================
# Prompt 拼装
# ============================================================

def build_rag_prompt(question: str, chunks: list[dict]) -> str:
    """
    把检索到的文档片段和用户问题拼装成 RAG Prompt
    """
    if not chunks:
        return f"用户问题：{question}\n\n（知识库中暂无相关文档，请如实告知用户。）"

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[来源: {chunk['source']}, 片段 #{chunk['chunk_index']}, "
            f"相关度: {chunk['score']}]\n{chunk['text']}"
        )

    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""你是一个文档问答助手。根据以下文档片段回答用户的问题。
如果文档中没有相关信息，请明确说明"文档中未找到相关信息"。
回答时要引用具体的文档来源。

相关文档片段：

{context}

用户问题：{question}

请用中文回答，并在回答中引用相关的文档来源。"""

    return prompt


# ============================================================
# 文档管理
# ============================================================

def delete_document(source: str, collection) -> bool:
    """
    从 ChromaDB 中删除指定文件名的所有块
    返回是否成功删除
    """
    try:
        # 查找该文档的所有块 ID
        existing = collection.get(where={"source": source})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
            return True
        return False
    except Exception as e:
        print(f"[delete_document] 删除失败: {e}")
        return False


def get_document_list(collection) -> list[str]:
    """获取当前已索引的文档文件名列表（去重）"""
    if collection.count() == 0:
        return []
    try:
        all_data = collection.get()
        sources = set()
        if all_data["metadatas"]:
            for meta in all_data["metadatas"]:
                sources.add(meta.get("source", "未知"))
        return sorted(sources)
    except Exception:
        return []


def get_collection_stats(collection) -> dict:
    """获取集合统计信息"""
    return {
        "document_count": len(get_document_list(collection)),
        "chunk_count": collection.count(),
    }


# ============================================================
# 工具函数
# ============================================================

def _make_chunk_id(source: str, chunk_index: int) -> str:
    """生成唯一的块 ID（去除特殊字符保证兼容性）"""
    safe_source = re.sub(r"[^a-zA-Z0-9_一-鿿.-]", "_", source)
    return f"{safe_source}_chunk_{chunk_index}"
