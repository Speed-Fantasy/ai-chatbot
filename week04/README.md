# 🤖 AI Agent

手写 Agent 循环，AI 自主决策调用工具完成任务。不用任何框架，从零理解 Agent 原理。

## 功能

- Agent 自主决策：分析问题 → 调工具 → 看结果 → 再决策 → 输出答案
- 7 个工具：计算器、读文件、写文件、列目录、Python 沙箱、查时间、文档检索
- 多轮对话记忆，上下文连续
- 工具调用过程可视（展开卡片查看参数和结果）

## 技术要点

- DeepSeek Tool Calling（原生 Function Calling）
- Agent Loop = while 循环 + API 调用 + 工具执行
- 安全沙箱：Python 代码执行带 AST 检查 + 黑名单

## 运行

```bash
pip install -r requirements.txt
streamlit run app.py
```
