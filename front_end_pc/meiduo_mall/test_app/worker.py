class Worker():
    # 任务执行
    def run(self, brokerobj, func):
        if func in brokerobj.func_list:
            return func()
        return None
