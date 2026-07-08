"""
Typora download and activate
python download and configure
Pycharm download and activate
"""
"""
利用终端查询python文件相关信息
利用终端运行py文件
"""
print('Hello World!\nHello Python!')
# 单行注释（井号后勿忘空格）
"""
多行注释
上下各三双引号或者三单引号
"""
# 变量声明赋值可同时，使用变量前勿忘赋值
name = 'kong'  # 直接声明和赋值
age = 20  # 无需声明数据类型
num1, num2, num3 = 1, 2, 3  # 多值同赋
num6 = 6
num7 = num6 + 1
sum_num = num1 + num2 + num3 + num6 + num7
print(sum_num, num1 + 1, '!')
print(type(name), type(1.9))  # type函数
print("name是否为int类型变量:", isinstance(name, int))  # isinstance函数
"""
标识符命名规则
a1 not 1a;can a_1,_1a
description and short
le_bron->蛇形命名法
"""
num7, num6 = num6, num7  # 无需中间变量
"""
关于常量
python中没有绝对常量
规定大写字母为常量，本质可改，但约定不改
"""
"""
定义二进制数0b,0B开头,用bin(num)转换进制
   八进制数0o,0O开头，用oct(num)转换进制
   十进制数无特定开头,用num表示
   十六进制数0x,0X开头,用hex(num)转换进制
"""
# print间内置换行，结尾处有end = "\n" 若想取消这一机制 需在结尾加上end = ""