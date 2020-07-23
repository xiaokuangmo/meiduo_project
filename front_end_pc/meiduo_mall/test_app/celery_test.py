from test_app.broker import Broker
from test_app.worker import Worker

# class A():
#     a=10
#
# class B():
#     b=20
#     a_obj=A()
# B().a_obj.a

class Celery():

    def __init__(self):
        self.worker = Worker()
        self.broker = Broker()

    def add(self, func):
        # 添加任务
        self.broker.func_list.append(func)

    def delay(self, func):
        # 执行方法
        return self.worker.run(self.broker, func)


# 生产者
def a_func():

    return 'a_func'

# 生成celery对象
celery=Celery()
# 添加任务
celery.add(a_func)
# 执行任务
data=celery.delay(a_func)
print(a_func)