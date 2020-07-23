import json
import re

from django.core.mail import send_mail
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
# 导入用户模型类进行用户表查询
from django_redis import get_redis_connection
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as TJS

from carts.utils import cart_goods
from user.models import User
from celery_tasks.emails.tasks import send_email


# Create your views here.
class UserNameView(View):
    """
        判断用户名是否重复
    """

    def get(self, request, username):
        """

        :param request: 请求报文对象
        :param username: 前端传递的用户名信息
        :return: 返回查询到的用户数量 count
        """
        # 1、根据前端传递的用户名查询用户数据库 count统计查询集中数据的数量
        try:
            # 在查询数据库是，可能会出现未知错误，为了保证代码正常运行，需要一场捕获
            count = User.objects.filter(username=username).count()
        except Exception as e:
            return JsonResponse({
                'code': 400,  # 自定义状态码 公司有自己状态码需求 900 987 857，statu返回的是http协议中 状态码100，200，300，400，500，
                'errmsg': e
            }, status=400)
        return JsonResponse({
            'count': count
        })


class MobilesView(View):
    """
        手机号重复判断
    """

    def get(self, request, mobile):
        """

        :param request: 请求报文对象
        :param mobile: 前端传递的手机号信息
        :return: 返回查询到的手机号数量 count
        """
        # 1、根据前端传递的用户名查询用户数据库 count统计查询集中数据的数量
        try:
            # 在查询数据库是，可能会出现未知错误，为了保证代码正常运行，需要一场捕获
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            return JsonResponse({
                'code': 400,  # 自定义状态码 公司有自己状态码需求 900 987 857，statu返回的是http协议中 状态码100，200，300，400，500，
                'errmsg': e
            }, status=400)
        return JsonResponse({
            'count': count
        })


class RegisterView(View):
    """
        用户注册
    """

    def post(self, request):
        # 1、获取前端数据 json
        # username	string	是	用户名
        # password	string	是	密码
        # password2	string	是	确认密码
        # mobile	string	是	手机号
        # sms_code	string	是	短信验证码
        # allow
        # 1-1 获取json数据
        data = request.body.decode()
        # 1-2 将json数据转化为字典数据
        data_dict = json.loads(data)
        password = data_dict.get('password')
        password2 = data_dict.get('password2')
        mobile = data_dict.get('mobile')
        allow = data_dict.get('allow')
        username = data_dict.get('username')
        sms_code = data_dict.get('sms_code')
        # 2、验证数据
        # 2-1、验证数据是否完整
        if not all([password2, password, mobile, allow, username, sms_code]):
            return JsonResponse({'errmsg': '数据错误'}, status=400)

        # 2-2、验证两次密码是否一致
        if password != password2:
            return JsonResponse({'errmsg': '数据错误'}, status=400)
        # 2-3、验证短信验证是否一致 查询reids进行比对
        conn_sms = get_redis_connection('sms_code')
        real_sms = conn_sms.get('sms_code_%s' % mobile)
        real_sms_str = real_sms.decode()
        if sms_code != real_sms_str:
            return JsonResponse({'errmsg': '数据错误'}, status=400)
        # 2-4 验证手机格式
        if not re.match('1[3-9]\d{9}', mobile):
            return JsonResponse({'errmsg': '数据错误'}, status=400)
        # 2-5 验证用户名长度
        if not re.match('[\w-]{5,20}', username):
            return JsonResponse({'errmsg': '数据错误'}, status=400)
        # 3、保存数据 导入用户表进行保存
        user = User.objects.create_user(username=username, password=password, mobile=mobile)

        # 写入session完成用户信息记录，可以使用Django自带方法login完成状态保持
        login(request, user)
        # 注册时需要将用户名信息写入cookie方便进行前端展示
        response = JsonResponse({'msg': 'ok', 'code': 0})
        response.set_cookie('username', user.username, max_age=3600 * 24 * 14)
        # 4、返回结果'code':0 告诉前端进行跳转
        return response


class LoginView(View):
    """
        登录
    """

    def post(self, request):

        # 1、获取前端数据 json
        # username	string	是	用户名
        # password	string	是	密码
        # remembered
        data = request.body.decode()
        data_dict = json.loads(data)
        username = data_dict.get('username')
        password = data_dict.get('password')
        remembered = data_dict.get('remembered')

        # 2、判断用户名和密码 请求体 json 表单 文件
        if not all([password, username]):
            return JsonResponse({'errmsg': '数据错误'}, status=400)

        # 3、判断段用户是否存在 借助Django的authenticate方法完成用户和密码的判断，如果判断存在则返回用户对象，如果不存在则返回空
        user = authenticate(request, username=username, password=password)

        if not user:
            # 用户不存在
            return JsonResponse({'errmsg': '用户名或密码错误'}, status=400)

        # 记录用户的登录状态
        login(request, user)

        # 3、判断是否记住登录
        response = JsonResponse({'msg': 'ok', 'code': 0})
        if remembered:
            # 写入cookie数据
            # 如果需要记住登录则设置为None表示使用默认的两周
            request.session.set_expiry(None)
            response.set_cookie('username', user.username, max_age=3600 * 24 * 14)

            response = cart_goods(request, response, user)
            return response
        else:
            # 写入cookie数据
            # 0 表示不设置有效期，用户关闭页面的清除登录保存的数据
            request.session.set_expiry(0)
            response.set_cookie('username', user.username)

            response = cart_goods(request, response, user)
            return response


class LogOutView(View):
    """
        退出登录
    """

    def delete(self, request):
        # 1、删除redis中存储的session
        logout(request)
        # 2、删除cookie中存储的用户信息
        response = JsonResponse({'msg': 'ok', 'code': 0})
        # 删除cookie
        response.delete_cookie('username')

        return response


class InfoView(View):
    """
        获取登录的用户信息
    """

    def get(self, request):
        # 1、获取当前登录的用户对象
        user = request.user

        # 2、通过用户对象查询用户信息返回

        return JsonResponse({
            'code': 0,
            'msg': 'ok',
            "info_data": {
                "username": user.username,
                "mobile": user.mobile,
                "email": user.email,
                "email_active": user.email_active
            }
        })


class EmailView(View):
    """
        保存用户邮箱信息
    """

    def put(self, request):
        # 1、获取当前登录用户
        user = request.user
        # 2、对用户的邮箱字段更新 需要获取前端传递的邮箱地址
        data = request.body.decode()
        data_dict = json.loads(data)
        email = data_dict.get('email')
        user.email = email
        user.save()

        # 发送邮件
        # 第一个参数：邮箱标题
        # 第二个参数：邮箱的正文内容
        # 第三个参数：用户看到的发件人信息
        # 第四个参数：收件人的邮箱地址
        # 第五个参数：可以使用html的格式文本
        # a='尊敬的用户：您的验证地址为：<a href="http://www.baidu.com">百度链接</a>'
        # send_mail('美多验证','',settings.EMAIL_FROM,['3442367443@qq.com'],html_message=a)

        # 对用户信息进行加密生成一个加密字符串放到跳转链接中方便进行后续的邮箱验证
        data = {'id': user.id, 'email': user.email}
        tjs = TJS(settings.SECRET_KEY, 300)
        token = tjs.dumps(data).decode()

        # 异步发送短信
        send_email.delay(token, email)

        # 3、返回结果
        return JsonResponse({'code': 0})


class EmailVerifyView(View):
    """
        邮箱验证
    """

    def put(self, request):
        # 1、获取前端数据  token
        token = request.GET.get('token')
        # 2、解密验证token数据
        tjs = TJS(settings.SECRET_KEY, 300)
        try:
            data = tjs.loads(token)
        except:
            return JsonResponse({'code': 400, 'errmsg': '用户邮箱验证错误'}, status=400)
        # 提取加密的用户id和用户邮箱
        id = data.get('id')
        email = data.get('email')
        try:
            # 使用id 查询用户是否存在，get方查询不到回抛出异常
            user = User.objects.get(id=id)
        except:
            return JsonResponse({'code': 400, 'errmsg': '用户邮箱验证错误'}, status=400)

        if user.email != email:
            return JsonResponse({'code': 400, 'errmsg': '用户邮箱验证错误'}, status=400)

        # 3、验证成功则修改用户的邮箱验证字段
        user.email_active = True
        user.save()
        # 4、返回结果
        return JsonResponse({'code': 0, 'msg': 'pk'})


class CPassWordView(View):

    def put(self, request):
        # 1、获取
        # old_password	string	是	老密码
        # new_password	string	是	新密码
        # new_password2前端数据
        data = request.body.decode()
        data_dict = json.loads(data)
        old_password = data_dict.get('old_password')
        new_password = data_dict.get('new_password')
        new_password2 = data_dict.get('new_password2')
        # 2、验证数据
        if not all([old_password, new_password, new_password2]):
            return JsonResponse({'code': 400, 'errmsg': '数据错误'}, status=400)

        # 校验密码
        user = request.user
        if not user.check_password(old_password):
            return JsonResponse({'code': 400, 'errmsg': '密码错误'}, status=400)
        # 比较两次密码
        if new_password != new_password2:
            return JsonResponse({'code': 400, 'errmsg': '密码不一致'}, status=400)

        # 3、更新数据
        user.set_password(new_password)
        user.save()
        # 4、退出登录
        # 删除redis中存储的session
        logout(request)
        # 删除cookie中存储的用户信息
        response = JsonResponse({'msg': 'ok', 'code': 0})
        # 删除cookie
        response.delete_cookie('username')
        # 5、返回结果
        return response
