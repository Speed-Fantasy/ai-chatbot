"""
while循环语句
有四个部分：计数器初始化，循环条件，循环体，计数器变化
while—else语句
while结束执行后 执行else 退出while激活else除非有break
"""
# 使用while计算1～10之和
num = 0
i = 1 #  计数器初始化
while i <= 10: #  循环条件
    num += i #  循环体
    i += 1 #  计数器变化
else:print("计算已完成")
print(f"和为{num}\n程序结束")    