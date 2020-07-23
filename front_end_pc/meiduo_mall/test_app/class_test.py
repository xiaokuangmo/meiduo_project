class A():
    num = 10
    def __init__(self):
        self.name = 'python'


a = A()
a.age=20

def func(obj):

    print(a.num)
    print(a.name)
    print(a.age)


func(a)



