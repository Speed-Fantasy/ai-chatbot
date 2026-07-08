"""
break关键字 用于循环中 中断循环 接下来未执行的循环不再执行
else属于循环体一部分 也不会执行
"""
a = [2,8,6,3,5,3,1,0]
# 打印表a 要求遇到5停止打印a
for i in a:
    if i == 5:
        break
    print(i, end=" ")
print("程序结束")


for i in range(4):
    print(i, end=" ")
else:
    print("19")

for i in range(4):
    print(i, end=" ")
    break
else:
    print("19")