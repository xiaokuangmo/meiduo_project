import json
import re

from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from QQLoginTool.QQtool import OAuthQQ
from django.contrib.auth import login
# 可以通过settings获取配置文件信息
from django.conf import settings
from django_redis import get_redis_connection
from user.models import User

from oauth.models import OAuthQQUser
from itsdangerous import TimedJSONWebSignatureSerializer as TJS


# Create your views here.
class QQLoginView(View):

    def get(self, request):
        """
            生成qq登录的跳转链接
        :param request:
        :return:
        """
        # 1、调用QQ登录的SDK包，构建qq的登录对象
        # 前端通过查询字符串next参数传递了一个状态值
        state = request.GET.get('next')
        if state is None:
            state = '/'
        qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                     redirect_uri=settings.QQ_REDIRECT_URI, state=state)

        # 2、使用qq对象生成跳转链接
        qq_login = qq.get_qq_url()

        return JsonResponse({'code': 0, 'login_url': qq_login})


class QQCallBackView(View):

    def get(self, request):
        # 1、获取前端数据 code值
        code = request.GET.get('code')
        # 2、验证数据 验证code是否前端真的传递
        if code is None:
            return JsonResponse({'code': 400, 'errmsg': '未传递code值'}, status=400)

        # 3、通过获取code值获取access_token值
        # 3-1 生成qq连接对象
        qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                     redirect_uri=settings.QQ_REDIRECT_URI, state='/')
        # 3-2 用qq对象调用方法获取access_token
        access_token = qq.get_access_token(code)
        # 4、通过获取access_token值获取openid值
        openid = qq.get_open_id(access_token)

        # 5、通过获取的openid判断qq用户是否已经绑定过美多账户，get查询数据时，如果数据不存在则抛出异常，所有如果捕获到异常，说明未查询到用户绑定
        try:
            qq_user = OAuthQQUser.objects.get(openid=openid)
        except:
            # 7、捕获到异常说明用户未绑定
            # 则需要引导用户进入绑定页面进行第三步绑定操作
            # 为了保证数据的安全性，需要对openid进行加密
            data = {'openid': openid}
            # 第一个参数是密钥，可以使用Django自带的密钥,第二个参数指定加密数据的有效期
            tjs = TJS(settings.SECRET_KEY, 300)
            access_token = tjs.dumps(data).decode()
            return JsonResponse({'msg': 'ok', 'access_token': access_token})
        # 6、如果已经绑定，则登录功，写入登录状态信息 已获取qq_user，获取美多用户对象user qq_user.user
        # 获取用户对象user
        user = qq_user.user
        login(request, user)
        # 将用户名信息写入cookie
        response = JsonResponse({'msg': 'ok', 'code': 0})
        response.set_cookie('username', user.username, max_age=3600 * 24 * 14)
        return response

    def post(self, request):
        """
            QQ第三步，数据绑定
        :param request:
        :return:
        """
        # 1、获取前端传递的数据 json
        data = request.body.decode()
        data_dict = json.loads(data)
        mobile = data_dict.get('mobile')
        password = data_dict.get('password')
        sms_code = data_dict.get('sms_code')
        access_token = data_dict.get('access_token')

        # 2、验证数据
        if not all([mobile, password, sms_code, access_token]):
            return JsonResponse({'code': 400, 'errmsg': '数据不完整'}, status=400)

        # 解密openid
        tjs = TJS(settings.SECRET_KEY, 300)
        # 如果数据已失效，则在解密会抛出异常
        try:
            data = tjs.loads(access_token)
        except:
            return JsonResponse({'code': 400, 'errmsg': '数据错误'}, status=400)
        openid = data.get('openid')

        # 验证手机格式
        if not re.match('1[3-9]\d{9}', mobile):
            return JsonResponse({'errmsg': '数据错误'}, status=400)

        # 验证输入短信验证码
        conn_sms = get_redis_connection('sms_code')
        real_sms = conn_sms.get('sms_code_%s' % mobile)
        real_sms_str = real_sms.decode()
        if sms_code != real_sms_str:
            return JsonResponse({'errmsg': '数据错误'}, status=400)
        # 3、判断手机号对应的用户是否存在
        try:
            user = User.objects.get(mobile=mobile)
        except:
            # 4、判断手机号对应的用户是否不存在
            #    使用该手机号注册新用户
            user = User.objects.create_user(username=mobile, mobile=mobile, password=password)

        # 3-1用户存在则校验密码
        if not user.check_password(password):
            return JsonResponse({'errmsg': '密码错误'}, status=400)
        # 3-2密码正确则将openid和美多用户存储到表中进行绑定
        OAuthQQUser.objects.create(user=user, openid=openid)

        # 绑定成功则登录成功
        login(request, user)
        response = JsonResponse({'code': 0, 'msg': 'ok'})
        response.set_cookie('username', user.username, max_age=3600 * 24 * 14)

        return response
