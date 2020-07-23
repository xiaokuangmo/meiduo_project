from django.shortcuts import render
from django.views import View
from django.http import HttpResponse, JsonResponse
from django_redis import get_redis_connection

from meiduo_mall.libs.captcha.captcha import captcha
from meiduo_mall.libs.yuntongxun.ccp_sms import CCP
from random import randint

from celery_tasks.sms.tasks import send_sms

# Create your views here.
class ImageView(View):
    """
        获取图片验证码
    """

    def get(self, request, uuid):
        """

        :param request:
        :param uuid: 前端传递的图片编号，方便后续进行验证码验证，获取真实的验证码信息
        :return:
        """

        # 1、调用三方验证码生成包生成图片验证 text 文本的验证码 图片的验证
        text, img = captcha.generate_captcha()

        # 2、保存生成后的图片验证，将验证码数据保存redis中（验证码信息不需要长期保存，在redis中可以设置有效期）
        # 2-1 建立redis链接对象 参数是在配置问价那种的指定库名
        conn = get_redis_connection('veify')
        # 2-2 写入生成的验证码信息 setex写入字符串数据并指定有效期
        conn.setex('img_%s' % uuid, 300, text)
        print(text)

        # 3、返回图片验证码
        return HttpResponse(img, content_type='image/jpg')


class SendSMSView(View):
    """
        发送短信
    """

    def get(self, request, mobile):

        # 判断redis中有没有flag数据，如果有说明已经发送短信
        conn_sms = get_redis_connection('sms_code')
        flag = conn_sms.get('flag_%s' % mobile)
        if flag:
            return JsonResponse({"errmsg": '请勿频繁发送'}, status=400)

        # 1、接受前端传递的数据内容 手机号，用户输入的验证以及图片验证码id
        image_code = request.GET.get('image_code')  # 用户输入的
        image_code_id = request.GET.get('image_code_id')  # 图片验证码的id
        # 2、验证用户输入的验证码和实际生成的是否一直
        # 2-1 从redis中获取保存在redis中的真实验证码
        conn = get_redis_connection('veify')
        real_code = conn.get('img_%s' % image_code_id)  # 获取的real_code值是bytes类型
        real_code_str = real_code.decode()
        # 2-2 比对用户输入的和真实的验证码
        if image_code.lower() != real_code_str.lower():
            return JsonResponse({'code': 400, 'errmsg': '两个验证码不一致'}, status=400)

        # 3、发送短信
        # 3-1 生成短信验证码，借助random随机生成
        sms_code = randint(0, 999999)
        print(sms_code)
        # 3-2 将验证码保存在redis中
        # conn_sms.setex('sms_code_%s' % mobile, 300, str(sms_code))
        # # 3-3 写入一个60s有效期的判断数据
        # conn_sms.setex('flag_%s' % mobile, 60, 'flag')

        # 使用reids管道
        # 先生成管道对象
        pline = conn_sms.pipeline()
        pline.setex('sms_code_%s' % mobile, 300, str(sms_code))
        pline.setex('flag_%s' % mobile, 60, 'flag')
        pline.execute()
        # 3-3 调用容联云发送短信
        # data = CCP().send_template_sms(mobile, [str(sms_code), 5], 1)
        # 为了避免网络阻塞，造成发送短信阻塞当先线程执行，可以采用异步形式发送短信
        send_sms.delay(mobile,sms_code)
        # 4、返回ok
        return JsonResponse({'msg': 'ok'})
