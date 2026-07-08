"""
     基本if选择结构 根据已知条件 进行判断
      如果条件成立 则执行结构内代码 然后执行结构外代码
"""
print("请输入年龄：")
exam = input()
if exam.isdigit():
    age = int(exam)
    if age >= 18:
        print("你已成年！")
    elif 18 > age >= 0:  #elif十分重要，如果是if的话，若不满足会执行下个else语句
        print("你未成年！")
    else:
        print("岁数不符合要求!你错过了鉴定机会！")
else:
    print("输入格式不对,你错过了鉴定机会！")
