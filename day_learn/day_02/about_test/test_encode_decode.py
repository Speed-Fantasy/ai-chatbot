"""
encode函数根据指定格式进行编码
decode函数根据指定格式进行解码
字母和中文单个都占多少字节由编码表决定
GB2312与GBK 一个中文占2个字节
UTF-8 一个中文占3个字节 最常用
"""
s1 = "abc口令扩"
s1_bytes = s1.encode("utf-8")
print(s1_bytes)
print(s1.encode("gbk"))
print(type(s1_bytes))
# len用于获取长度
print(len(s1_bytes))
print(s1_bytes.decode("utf-8"))
print(type(s1_bytes.decode("utf-8")))
print(len(s1_bytes.decode("utf-8")))