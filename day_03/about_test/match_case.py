"""
match-case结构 用于处理某个值
用于处理固定等值的情况
"""
num = int(input("请输入你本次抽中的序号："))
match num:
    case 1:   #满足case就执行并退出match结构
        print("一台保时捷")
    case 2:
        print("一台迈巴赫")
    case 3:
        print("一台奥迪S1")
    case _:    #case _必执行
        print("您未中奖") 
print("谢谢参与")    

month = int(input("请输入查询月份（纯数字）："))
if 0 < month <= 12:
    match month:
        case 1 | 3 | 5 | 7 | 8 | 10 | 12:
            print(f"{month}月有31天") 
        case 2:
            year = int(input("请输入查询年份（纯数字）："))
            if (year % 4 == 0) and (year % 100 != 0 or year % 400 ==0):
                print(f"{year}年的{month}月有29天")
            else:
                print(f"{year}年的{month}月有28天")
        case _:
            print(f"{month}月有30天")
else:
    print("输入月份不符合要求！结束程序!")
print("感谢使用，程序结束!")            