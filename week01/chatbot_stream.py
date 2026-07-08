from openai import OpenAI

client = OpenAI(
    api_key="sk-abfe4f5174fb451ca733b0f7728bbb3f",
    base_url="https://api.deepseek.com",
)

messages = []

print("流式聊天机器人已启动！输入 quit 退出\n")

while True:
    user_input = input("你：")
    if user_input == "quit":
        break

    messages.append({"role": "user", "content": user_input})

    # stream=True：AI 一个字一个字返回，不等整段生成完
    stream = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=True,
    )

    # 收集完整回复，同时一个字一个字打印
    print("AI：", end="", flush=True)
    full_reply = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            print(text, end="", flush=True)   # end="" 不换行，一个字接一个字打印
            full_reply += text

    messages.append({"role": "assistant", "content": full_reply})
    print("\n")
