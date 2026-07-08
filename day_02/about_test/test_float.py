"""
浮点数一般使用IEEE 754标准
利好cpu统一使用此标准运行效率高，但容易出现精度损失(cpu缺陷，二进制计算浮点数不准)
导入Decimal可以解决精度问题，满足精度要求
Decimal这个类自带十进制运算算法，利用字符串绕开cpu计算
"""
from decimal import Decimal
# 从decimal标准库引入Decimal类
num1 = 0.1
num2 = 0.2
print(num1 + num2)  # 计算结果为0.30000000000000004(精度损失)
num3 = Decimal('0.1')  #字符串传给此类处理该数
num4 = Decimal('0.2')  #此类传回来全新数据类型
print(num3 + num4)  # 两变量为decimal.Decimal类型数据，实现精确计算
print(str(num1) == '0.1')  # 用str函数取变量a的字符串形式