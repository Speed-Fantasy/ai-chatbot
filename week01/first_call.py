from openai import OpenAI

client = OpenAI(
    api_key="sk-abfe4f5174fb451ca733b0f7728bbb3f",
    base_url="https://api.deepseek.com",
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": "用一句话解释什么是向量数据库"}
    ],
)

reply = response.choices[0].message.content
print(reply)
