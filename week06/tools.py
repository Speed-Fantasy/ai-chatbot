"""
知识库 Agent 工具集
包含 Week04 全部工具 + 新增 search_docs（RAG 检索）
"""
import sys
import os
import importlib.util

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)

# ============================================================
# 用 importlib 显式加载 Week04 工具（避免循环导入）
# ============================================================
_w4_path = os.path.join(_parent_dir, "week04", "tools.py")
_spec = importlib.util.spec_from_file_location("week04_tools_pkg", _w4_path)
_w4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_w4)

# 从 Week04 导出所有工具函数
calculator = _w4.calculator
get_current_time = _w4.get_current_time
read_file = _w4.read_file
list_files = _w4.list_files
python_repl = _w4.python_repl
write_file = _w4.write_file

# ============================================================
# 引入 Week03 RAG 引擎
# ============================================================
_week03 = os.path.join(_parent_dir, "week03")
if _week03 not in sys.path:
    sys.path.insert(0, _week03)

from rag_core import (
    init_embedding_model, init_chroma_client, reset_chroma_db,
    extract_text, chunk_document, index_chunks, retrieve,
    get_document_list, get_collection_stats, delete_document,
    DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP,
)

# ============================================================
# 新增工具：search_docs
# ============================================================

_embedding_model = None
_chroma_collection = None


def setup_rag(collection, model):
    global _chroma_collection, _embedding_model
    _chroma_collection = collection
    _embedding_model = model


def search_docs(query: str, top_k: int = None) -> str:
    """在已上传文档中语义搜索相关内容"""
    if _chroma_collection is None or _embedding_model is None:
        return "知识库未初始化，请先上传文档"
    if _chroma_collection.count() == 0:
        return "知识库中没有文档"

    k = top_k or 4
    try:
        results = retrieve(query, _chroma_collection, _embedding_model, top_k=k)
        if not results:
            return "未找到相关内容"
        lines = []
        for i, r in enumerate(results, 1):
            lines.append(
                f"[{i}] {r['source']} (片段#{r['chunk_index']}, "
                f"相关度: {r['score']})\n{r['text'][:500]}"
            )
        return "\n\n---\n\n".join(lines)
    except Exception as e:
        return f"搜索失败：{e}"


# ============================================================
# 合并工具定义
# ============================================================

SEARCH_DOCS_DEF = {
    "type": "function",
    "function": {
        "name": "search_docs",
        "description": "在已上传的文档中语义搜索相关内容。当用户问文档中的信息时，必须用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词或问题"},
                "top_k": {"type": "integer", "description": "返回结果数量，默认4"},
            },
            "required": ["query"],
        },
    },
}

TOOL_DEFINITIONS = list(_w4.TOOL_DEFINITIONS) + [SEARCH_DOCS_DEF]

TOOL_MAP = {
    **_w4.TOOL_MAP,
    "search_docs": search_docs,
}
