"""
第一周 Python 速通 — 只学后面项目马上用到的
你已经有 C 和 Java 基础，重点关注 Python 不一样的写法
"""

# ============================================================
# 1. dict（字典）—— Python 里最重要的数据结构
#    对比 Java: 这就是 HashMap<String, Object>
#    后面调 API 返回的 JSON，全部变成 dict 给你
# ============================================================

# 定义一个 dict
result = {
    "name": "Claude",
    "tokens": 150,
    "is_streaming": True,
    "tags": ["AI", "LLM"]  # dict 里面可以放 list
}   # key需为字符串类型，映射对象随便

# 读取
print(result["name"])           # Claude
print(result.get("price", 0))   # 安全读取：不存在就返回默认值 0

# 遍历
for key, value in result.items():
    print(f"{key} = {value}")

print("---")

# ============================================================
# 2. list + dict 组合 —— API 返回的东西就长这样
# ============================================================

messages = [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮你？"},
]

# 遍历 list of dict
for msg in messages:
    print(f"[{msg['role']}]: {msg['content']}")

# 往 list 里追加
messages.append({"role": "user", "content": "讲个笑话"})
print(f"现在有 {len(messages)} 条消息")

print("---")

# ============================================================
# 3. 函数 —— 和 Java 最大的区别：动态类型
#    Python 不需要声明参数类型和返回值类型
# ============================================================

def call_ai(prompt, temperature=0.7):  # temperature 有默认值
    """模拟调用 AI API（后面会换成真 API）"""
    return f"AI 收到：「{prompt}」，温度={temperature}"

# 调用
reply = call_ai("解释什么是向量数据库")
print(reply)

# 只传必填参数，temperature 用默认值
reply2 = call_ai("讲个笑话")
print(reply2)

print("---")

# ============================================================
# 4. f-string —— 写 prompt 全靠它
#    f"..." 里面用 {变量} 直接拼字符串
# ============================================================

name = "张三"
job = "Python 后端开发"

# 拼一段 prompt
prompt = f"""
你是一个资深 HR，请帮 {name} 优化简历。
他应聘的是 {job} 岗位。
请从以下三个角度给出建议：
1. 技能亮点
2. 项目描述
3. 整体结构
"""
print(prompt)

print("---")

# ============================================================
# 5. 文件读写 + JSON
# ============================================================

import json

# 写 JSON 到文件
data = {
    "model": "claude-sonnet-5",
    "temperature": 0.7,
    "max_tokens": 1024
}

with open("config.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("已写入 config.json")

# 从文件读 JSON
with open("config.json", "r", encoding="utf-8") as f:
    loaded = json.load(f)
print(f"读取到: model={loaded['model']}, temperature={loaded['temperature']}")

print("---")

# ============================================================
# 6. 额外赠送两个会用到的
# ============================================================

# 列表推导式 —— Python 写循环的简洁写法
squares = [x**2 for x in range(1, 6)]
print(f"1-5 的平方: {squares}")  # [1, 4, 9, 16, 25]

# 异常处理
try:
    x = 1 / 0
except ZeroDivisionError:
    print("除零错误被捕获，程序没崩溃")

print("\n✅ 全部跑通！Python 基础够用了。")
