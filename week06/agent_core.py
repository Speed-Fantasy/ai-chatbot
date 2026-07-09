"""
Agent 循环引擎 — 知识库版
在 Week04 Agent 基础上增加文档检索能力
"""
import os
import sys
import json

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from tools import TOOL_DEFINITIONS, TOOL_MAP

SYSTEM_PROMPT = """你是一个文档处理专家 Agent。用户可以上传文档，你可以搜索、分析、提取、总结文档内容。

## 核心能力
- **search_docs**: 在已上传文档中语义搜索（最常用的工具！）
- read_file: 读取本地文件
- list_files: 列出目录文件
- write_file: 保存分析结果到文件
- calculator: 计算文档中的数据
- python_repl: 处理文档数据、统计分析
- get_current_time: 获取当前时间

## 工作原则
1. 用户问文档相关问题，**必须先 search_docs**
2. 引用时标注来源文件名和片段号
3. 一次搜不到就换关键词再搜
4. 能把分析结果写入文件保存
5. 用中文回答"""


def run_agent_streaming_answer(client, user_task, model="deepseek-chat",
                                temperature=0.1, max_iterations=10, history=None):
    """流式 Agent 循环：工具调用非流式，最终回答流式"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_task})

    tool_call_count = 0

    for iteration in range(1, max_iterations + 1):
        try:
            response = client.chat.completions.create(
                model=model, messages=messages, tools=TOOL_DEFINITIONS,
                temperature=temperature, stream=False,
            )
        except Exception as e:
            yield {"type": "error", "message": f"API 调用失败：{str(e)}"}
            return

        message = response.choices[0].message

        if message.tool_calls:
            messages.append(message)

            for tool_call in message.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                yield {"type": "tool_call", "name": name, "args": args, "iteration": iteration}

                func = TOOL_MAP.get(name)
                if func:
                    try:
                        result = func(**args)
                    except Exception as e:
                        result = f"工具执行异常：{str(e)}"
                else:
                    result = f"未知工具：{name}"

                tool_call_count += 1

                yield {"type": "tool_result", "name": name, "result": result}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

            continue

        # 最终回答 — 流式
        try:
            stream = client.chat.completions.create(
                model=model, messages=messages, temperature=temperature, stream=True,
            )
            full = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    t = chunk.choices[0].delta.content
                    full += t
                    yield {"type": "text_chunk", "content": t}

            yield {"type": "done", "answer": full, "iterations": iteration,
                   "tool_calls_count": tool_call_count}
            return
        except Exception as e:
            yield {"type": "error", "message": f"流式响应失败：{str(e)}"}
            return

    yield {"type": "error", "message": f"Agent 达到最大循环次数（{max_iterations}），已强制终止。"}
