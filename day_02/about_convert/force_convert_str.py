"""
str将传入数据转换成字符串
"""
a = 1
s1 = str(a)
print(s1)
print(type(s1))
age = 19
# 让int类型数据参与到字符串的合成中去，实现无缝输出
print("我今年" + str(age) + "岁")
# 使用{}标记符，f为格式化字符串，自动填充至字符串中
print(f"我今年{age}岁")
