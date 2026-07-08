from openai import OpenAI

client = OpenAI(
    api_key="sk-abfe4f5174fb451ca733b0f7728bbb3f",
    base_url="https://api.deepseek.com",
)

# messages 存所有对话历史，AI 靠这个"记住"你们聊了什么
messages = []

print("聊天机器人已启动！输入 quit 退出\n")

while True:
    user_input = input("你：")
    if user_input == "quit":
        break

    # 把用户说的话追加到历史
    messages.append({"role": "user", "content": user_input})

    # 把整个历史发给 AI
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
    )

    reply = response.choices[0].message.content

    # 把 AI 的回复也存进历史，下次接着用
    messages.append({"role": "assistant", "content": reply})

    print(f"AI：{reply}\n")
