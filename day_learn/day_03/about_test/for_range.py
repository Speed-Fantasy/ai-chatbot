"""
for循环用于遍历可迭代对象 如列表和字符串
"""
for i in range(4):  # i为临时变量
    print(i,end=" ")
print()
for i in "Hello, World!":
    print(i,end="")
print()
"""
range()函数
range([start,]stop[,step])
start默认为0 step默认为1
stop为开区间
"""
for i in range(1,10,2):  # i为临时变量
        print(i,end=" ")
print()
for i in range(10,0,-2):
    print(i,end=" ")