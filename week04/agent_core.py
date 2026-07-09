"""
Agent 循环引擎
核心逻辑：AI 决策 → 调工具 → 看结果 → 再决策 → ... → 给出最终答案
"""
import json
from openai import OpenAI
import os as _os
import sys as _sys
_current_dir = _os.path.dirname(_os.path.abspath(__file__))
if _current_dir not in _sys.path:
    _sys.path.insert(0, _current_dir)
from tools import TOOL_DEFINITIONS, TOOL_MAP

SYSTEM_PROMPT = """你是一个智能助手 Agent，可以调用工具来完成任务。

## 规则
1. 分析用户的问题，判断需要用什么工具
2. 调用工具获取结果
3. 根据工具结果回答问题
4. 如果工具结果不够，可以继续调用其他工具
5. 如果不需要工具就能回答，直接回答

## 可用工具
- **calculator**: 计算数学表达式
- **get_current_time**: 获取当前日期时间
- **read_file**: 读取文件内容
- **list_files**: 列出目录中的文件
- **python_repl**: 在安全沙箱中执行 Python 代码

## 注意事项
- 如果用户要求"计算"或询问数学问题，使用 calculator
- 如果用户问"现在几点"或"今天日期"，使用 get_current_time
- 如果用户要求"读文件"或"查看代码"，使用 read_file
- 如果用户要求"列出文件"或"看看有什么文件"，使用 list_files
- 如果用户要求"执行代码"或做数据处理，使用 python_repl
- 可以组合使用多个工具
- 用中文回答
- 记住对话历史，用户说的内容不会丢失"""


def run_agent(
    client: OpenAI,
    user_task: str,
    model: str = "deepseek-chat",
    temperature: float = 0.1,
    max_iterations: int = 10,
):
    """
    Agent 循环生成器：逐步执行 Agent 的决策过程

    参数:
        client: OpenAI 客户端（指向 DeepSeek）
        user_task: 用户的任务描述
        model: 模型名称
        temperature: 温度参数（Agent 建议低温度，保证确定性）
        max_iterations: 最大循环次数

    Yields:
        {"type": "tool_call", "name": ..., "args": ..., "iteration": N}
        {"type": "tool_result", "name": ..., "result": ...}
        {"type": "text", "content": ...}
        {"type": "done", "answer": ..., "iterations": N, "tool_calls_count": N}
        {"type": "error", "message": ...}
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_task},
    ]

    tool_call_count = 0

    for iteration in range(1, max_iterations + 1):
        # 调用 API（非流式，因为需要检查 tool_calls）
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                temperature=temperature,
                stream=False,
            )
        except Exception as e:
            yield {"type": "error", "message": f"API 调用失败：{str(e)}"}
            return

        choice = response.choices[0]
        message = choice.message

        # 检查是否 AI 要调工具
        if message.tool_calls:
            # 把 AI 的 tool_call 消息加入历史
            messages.append(message)

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # 通知 UI：正在调工具
                yield {
                    "type": "tool_call",
                    "name": tool_name,
                    "args": tool_args,
                    "iteration": iteration,
                }

                # 执行工具
                tool_func = TOOL_MAP.get(tool_name)
                if tool_func:
                    try:
                        result = tool_func(**tool_args)
                    except Exception as e:
                        result = f"工具执行异常：{str(e)}"
                else:
                    result = f"未知工具：{tool_name}"

                tool_call_count += 1

                # 通知 UI：工具结果
                yield {
                    "type": "tool_result",
                    "name": tool_name,
                    "result": result,
                }

                # 把工具结果加入历史
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

            # 继续循环，让 AI 看到工具结果后再决策
            continue

        # 没有 tool_calls，AI 在给最终回答
        content = message.content or ""

        if content.strip():
            yield {
                "type": "text",
                "content": content,
            }

        yield {
            "type": "done",
            "answer": content,
            "iterations": iteration,
            "tool_calls_count": tool_call_count,
        }
        return

    # 超过最大循环次数
    yield {
        "type": "error",
        "message": f"Agent 达到最大循环次数（{max_iterations}），已强制终止。请简化你的问题。",
    }


def run_agent_streaming_answer(
    client: OpenAI,
    user_task: str,
    model: str = "deepseek-chat",
    temperature: float = 0.1,
    max_iterations: int = 10,
    history: list = None,
):
    """
    流式 Agent：工具调用非流式，最终回答流式（打字机效果）

    history: 之前的对话历史（不含 system prompt），格式 [{"role":"user","content":"..."},{"role":"assistant","content":"..."},...]
             传入后 Agent 就能记住之前聊了什么
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_task})

    tool_call_count = 0

    for iteration in range(1, max_iterations + 1):
        # 非流式调用（检查 tool_calls）
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                temperature=temperature,
                stream=False,
            )
        except Exception as e:
            yield {"type": "error", "message": f"API 调用失败：{str(e)}"}
            return

        choice = response.choices[0]
        message = choice.message

        # AI 要调工具
        if message.tool_calls:
            messages.append(message)

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                yield {
                    "type": "tool_call",
                    "name": tool_name,
                    "args": tool_args,
                    "iteration": iteration,
                }

                tool_func = TOOL_MAP.get(tool_name)
                if tool_func:
                    try:
                        result = tool_func(**tool_args)
                    except Exception as e:
                        result = f"工具执行异常：{str(e)}"
                else:
                    result = f"未知工具：{tool_name}"

                tool_call_count += 1

                yield {
                    "type": "tool_result",
                    "name": tool_name,
                    "result": result,
                }

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

            continue

        # AI 给最终回答 — 用流式
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )

            full_answer = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_answer += token
                    yield {"type": "text_chunk", "content": token}

            yield {
                "type": "done",
                "answer": full_answer,
                "iterations": iteration,
                "tool_calls_count": tool_call_count,
            }
            return

        except Exception as e:
            yield {"type": "error", "message": f"流式响应失败：{str(e)}"}
            return

    yield {
        "type": "error",
        "message": f"Agent 达到最大循环次数（{max_iterations}），已强制终止。",
    }
