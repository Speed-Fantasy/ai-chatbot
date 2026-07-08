"""
bool中的true和false本质是int的1和0
延续c的设计
特别：所有的True同为一个对象，False也是
"""
i = True
p = False
print(type(i), type(p))
print(i == 1)
# print(isinstance(i, int))
print(p == 0)
# print(isinstance(p, int))
o = False
print(o == 0)
print(o is 0)
print(o is p)  # 全局单例对象
"""
空的集合，容器以及0.0.0，None都能当成False来用
"""
if not None:
    print("None被当作False")
# None也是全局单例对象，存在一个即可
