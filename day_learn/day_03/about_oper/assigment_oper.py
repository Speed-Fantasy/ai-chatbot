"""
赋值运算符
+=加法赋值
-=减法赋值
*=乘法赋值
**=幂赋值
/=除法赋值
//=整除赋值
%=模赋值
"""
# print(a := input() > 0)  会报错，因为input返回的是str类型，无法与0比较，可以用int函数转换
print(a := 1 > 0)  #优先判断再赋值
print(a)
print(a := 0 > 0)
print(a)
# print(a := input() > 0)  会报错，因为input返回的是str类型，无法与0比较，可以用int函数转换
print((a := 1) > 0)
print(a)