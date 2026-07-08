"""
continue关键字作用于循环 用于跳出本轮循环剩余语句 开始新一轮循环
结合分支结构使用
"""
print("用for打印1，2，3，4，6，7，8，9")
for i in range(1, 10):
    if i == 5:
        continue
    print(i, end=" ")