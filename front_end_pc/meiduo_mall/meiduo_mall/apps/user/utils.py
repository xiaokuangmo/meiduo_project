import re

from django.contrib.auth.backends import ModelBackend
from user.models import User


class UserBackend(ModelBackend):
    """
        重写Django原有的用户判断方法完成多账号登录
        在配置文件中告知Django重写后的方法
    """

    def authenticate(self, request, username=None, password=None, **kwargs):

        try:
            # 使用get方法查询，如果数据不存在则会抛出异常
            if re.match(r'1[3-9]\d{9}$', username):
                # 判断传递username是不是手机号
                # 正则匹配成功则说明是手机号，需要按照手机字段查询
                user = User.objects.get(mobile=username)
            else:
                user = User.objects.get(username=username)
        except:
            user = None

        if user and user.check_password(password):
            # 如果用户查询到并且校验密码正确 check_password Django提供的校验密码方法
            return user

