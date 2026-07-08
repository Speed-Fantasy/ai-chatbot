# AI 聊天机器人

Python + DeepSeek API 实现的命令行聊天机器人。

## 功能

- 命令行聊天，多轮对话，带记忆
- 流式输出（AI 逐字回复）
- 输入 `quit` 退出

## 运行

```bash
pip install openai
python chatbot_stream.py
```

## 技术栈

- Python
- DeepSeek API（OpenAI 兼容格式）

## 第一周学习笔记

| 文件 | 内容 |
|------|------|
| `week01/learn.py` | Python 基础（dict/list、函数、f-string、JSON、异常处理） |
| `week01/first_call.py` | 第一次 API 调用 |
| `week01/chatbot.py` | 带记忆的聊天机器人 |
| `week01/chatbot_stream.py` | 流式输出聊天机器人 |
