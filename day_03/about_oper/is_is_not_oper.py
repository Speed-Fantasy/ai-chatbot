"""
    身份运算符
    is 表示判断是否是同一个对象
    is not 表示 判断是否不是同一个对象
"""
a = 1
b = 1
print(a is b)
print(a is not b)
print(id(a), id(b))