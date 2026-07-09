"""
Agent 工具集合
每个工具返回一个字符串结果（成功或错误信息）
"""
import os
import ast
import operator
import math
from datetime import datetime

# Python REPL 安全白名单
_SAFE_BUILTINS = {
    "abs": abs, "all": all, "any": any, "bool": bool, "chr": chr,
    "dict": dict, "enumerate": enumerate, "filter": filter, "float": float,
    "int": int, "len": len, "list": list, "map": map, "max": max,
    "min": min, "ord": ord, "pow": pow, "range": range, "reversed": reversed,
    "round": round, "set": set, "sorted": sorted, "str": str, "sum": sum,
    "tuple": tuple, "zip": zip, "True": True, "False": False, "None": None,
}
_SAFE_MATH = {
    "math": math,
}

# 危险操作黑名单（精确匹配，避免误杀）
_BLOCKED_KEYWORDS = [
    "os.system", "os.popen", "os.remove", "os.rmdir", "os.unlink",
    "subprocess", "shutil", "sys.exit", "__import__",
    "eval(", "exec(", "compile(",
    "open(",  # 文件写入
    "globals()", "locals()", "getattr(", "setattr(",
    "importlib", "from os", "from sys", "from subprocess",
]


def calculator(expression: str) -> str:
    """
    安全计算数学表达式
    示例: "2**10 + 50" → "1074"
    """
    try:
        # 用 ast 安全解析，只允许数学运算
        tree = ast.parse(expression.strip(), mode="eval")
        for node in ast.walk(tree):
            # 禁止函数调用、属性访问等
            if isinstance(node, ast.Call):
                return f"错误：表达式中不允许函数调用"
            if isinstance(node, ast.Attribute):
                return f"错误：表达式中不允许属性访问"
        result = eval(compile(tree, "<calc>", "eval"), {"__builtins__": {}}, {})
        return str(result)
    except SyntaxError:
        return f"错误：表达式语法不正确"
    except ZeroDivisionError:
        return f"错误：不能除以零"
    except Exception as e:
        return f"计算错误：{e}"


def get_current_time(format: str = "%Y年%m月%d日 %H:%M:%S") -> str:
    """
    获取当前日期和时间
    format: 时间格式，默认 "%Y年%m月%d日 %H:%M:%S"
    """
    try:
        return datetime.now().strftime(format)
    except Exception as e:
        return f"获取时间失败：{e}"


def read_file(filepath: str, max_chars: int = 5000) -> str:
    """
    读取文件内容
    filepath: 文件路径（相对或绝对）
    max_chars: 最大返回字符数
    """
    try:
        if not os.path.exists(filepath):
            return f"文件不存在：{filepath}"
        if os.path.getsize(filepath) > 10 * 1024 * 1024:  # 10MB 限制
            return f"文件过大（超过10MB），无法读取"

        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        if len(content) > max_chars:
            content = content[:max_chars] + f"\n...(文件过长，已截断至{max_chars}字符，共{len(content)}字符)"

        return content if content.strip() else "(文件为空)"
    except PermissionError:
        return f"没有权限读取文件：{filepath}"
    except Exception as e:
        return f"读取文件失败：{e}"


def list_files(directory: str = ".") -> str:
    """
    列出目录中的文件和子目录
    directory: 目录路径，默认当前目录
    """
    try:
        if not os.path.exists(directory):
            return f"目录不存在：{directory}"
        if not os.path.isdir(directory):
            return f"这不是一个目录：{directory}"

        items = os.listdir(directory)
        if not items:
            return "(空目录)"

        lines = []
        for name in sorted(items):
            full_path = os.path.join(directory, name)
            tag = "[DIR]" if os.path.isdir(full_path) else "[FILE]"
            size = ""
            if os.path.isfile(full_path):
                size_bytes = os.path.getsize(full_path)
                if size_bytes < 1024:
                    size = f"({size_bytes}B)"
                elif size_bytes < 1024 * 1024:
                    size = f"({size_bytes/1024:.1f}KB)"
                else:
                    size = f"({size_bytes/1024/1024:.1f}MB)"
            lines.append(f"{tag} {name} {size}")

        return "\n".join(lines)
    except PermissionError:
        return f"没有权限访问目录：{directory}"
    except Exception as e:
        return f"列出文件失败：{e}"


def write_file(filepath: str, content: str) -> str:
    """
    创建或覆盖写入文件
    filepath: 文件路径（如桌面路径或当前目录下）
    content: 要写入的内容
    """
    try:
        # 安全检查：禁止写入系统目录
        dangerous_dirs = ["C:\\Windows", "C:\\Windows\\System32", "/etc", "/bin", "/usr"]
        abs_path = os.path.abspath(filepath)
        for d in dangerous_dirs:
            if abs_path.lower().startswith(d.lower()):
                return f"安全拦截：禁止写入系统目录 {d}"

        # 限制文件大小
        if len(content) > 100000:
            return f"文件过大（{len(content)} 字符），最多允许 100000 字符"

        # 确保目录存在
        dir_name = os.path.dirname(abs_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"文件已成功创建：{abs_path}（{len(content)} 字符）"
    except PermissionError:
        return f"没有权限写入：{filepath}"
    except Exception as e:
        return f"写入文件失败：{e}"


def python_repl(code: str) -> str:
    """
    在安全沙箱中执行 Python 代码
    只允许基本运算和内置函数，禁止文件操作和系统调用
    """
    # 1. 关键词黑名单检查
    code_lower = code.lower()
    for keyword in _BLOCKED_KEYWORDS:
        if keyword in code_lower:
            return f"安全拦截：代码中包含危险操作 '{keyword}'"

    # 2. 多行代码检查（只允许单行表达式或简单语句）
    lines = [l for l in code.strip().split("\n") if l.strip() and not l.strip().startswith("#")]
    if len(lines) > 5:
        return "安全拦截：代码行数超过5行"

    # 3. AST 安全检查
    try:
        tree = ast.parse(code.strip(), mode="exec")
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                return "安全拦截：不允许 import 语句"
            if isinstance(node, ast.ImportFrom):
                return "安全拦截：不允许 from...import 语句"
    except SyntaxError:
        pass  # 可能单行表达式，用 eval 试

    # 4. 在受限环境中执行
    safe_globals = {"__builtins__": _SAFE_BUILTINS, **_SAFE_MATH}

    try:
        # 先尝试作为表达式求值
        try:
            expr_tree = ast.parse(code.strip(), mode="eval")
            result = eval(compile(expr_tree, "<repl>", "eval"), safe_globals, {})
            return str(result)
        except SyntaxError:
            pass

        # 再尝试作为语句执行（捕获 print 输出）
        import io
        stdout = io.StringIO()
        safe_globals["print"] = lambda *a, **k: print(*a, **k, file=stdout)
        exec(compile(code.strip(), "<repl>", "exec"), safe_globals, {})
        output = stdout.getvalue()
        return output if output else "(代码执行完毕，无输出)"
    except Exception as e:
        return f"执行错误：{type(e).__name__}: {e}"


# ============================================================
# 工具注册表
# ============================================================

# OpenAI/DeepSeek 兼容的 tools 定义
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "安全计算数学表达式，支持 + - * / ** () 等基本运算",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '2**10 + 50' 或 '(15+8)*3'",
                    },
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前日期和时间",
            "parameters": {
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "description": "时间格式，默认 '%Y年%m月%d日 %H:%M:%S'",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取本地文件内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "文件路径（相对或绝对）",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "最大返回字符数，默认5000",
                    },
                },
                "required": ["filepath"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "列出目录中的文件和子目录",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "目录路径，默认 '.' 表示当前目录",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "python_repl",
            "description": "在安全沙箱中执行 Python 代码，支持计算、数据处理、字符串操作等",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "要执行的 Python 代码，如 'sum(range(100))' 或 'sorted([3,1,2])'",
                    },
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "创建或覆盖写入文件到磁盘。可以用来保存内容、创建文本文件等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "文件路径，如 'C:\\Users\\你的用户名\\Desktop\\自我介绍.md'",
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的文件内容",
                    },
                },
                "required": ["filepath", "content"],
            },
        },
    },
]

# 工具名 → 函数映射
TOOL_MAP = {
    "calculator": calculator,
    "get_current_time": get_current_time,
    "read_file": read_file,
    "list_files": list_files,
    "python_repl": python_repl,
    "write_file": write_file,
}
