from django.core.files.storage import Storage


class FDFSStorage(Storage):
    # 判断文件是否重复
    def exists(self, name):
        return False

    def save(self, name, content, max_length=None):
        # 不需要保存 pass
        pass

    def url(self, name):
        # 拼接url路径 name 就是数据库中保存的图片路径
        return 'http://10.211.55.35:8888/' + name
