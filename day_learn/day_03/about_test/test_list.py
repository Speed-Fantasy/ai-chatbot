"""
列表创建 list = [o1,o2]
索引对应值获取 list[i]
取列表切片 list[i1:i2]
列表填加元素 append(i,o)
列表间相加 l1 + l2
列表乘法 list * int
列表改值 list[i] = o
检测某值列表是否有 o in list
获取列表长度 len(list)
取最大最小值及和 max(list),min(list),sum(list)
"""
list0 = [1, 2, 3, 4, 5]

print(list0)
print(list0[0])
print(list0[-1])

print(list0[1:-1])
print(list0[2:])
print(list0[:-2])

list0.append(7)
print(list0)
list0.insert(5, 6)
print(list0)

list1 = [8,9]
print(list0 + list1)
print(list1 * 2)
