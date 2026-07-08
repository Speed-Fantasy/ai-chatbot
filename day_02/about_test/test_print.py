"""
print函数输出内容默认打印完后换行
如果不想换行，可以指定end参数的值，来实现打印完之后的效果
"""
print("1")
print("2")
print("3")
print("1", end="")
print("2", end="")
print("3", end="\n")

# %占位符用法，旧式占位符
print("%d, %.4f" % (1, 2))

# {}格式占位符号，"".format()函数
print("{}, {}".format(1, 2))
s1 = "{}, {}"
print(s1.format(1, 2))
s2 = "{}, {}".format(1, 2)
print(s2)
s3 = "{1}, {0}".format(1, 2)
print(s3)

# 数字格式化
print('{:*^10,.1f}'.format(19))
# <,^,>分别是左对齐，居中，右对齐

# 常用写法
a = 1
b = 2
print(f"{a},{b}")
