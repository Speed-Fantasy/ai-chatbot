name = input("请输入你的名字:")
print(name,"，你好啊!")
Flag = input("你今天是否开心？true or false?")
if Flag == "true":
    print("开开心心每一天！Love Life")
if Flag == "false":
    print("别不开心嘛，请热爱生活")
if Flag not in  ("true", "false"):
    print("请重新输入，true or false?")
