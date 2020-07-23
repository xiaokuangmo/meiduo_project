from django.conf.urls import re_path
from . import views
urlpatterns =[
    # 图片验证码的获取
    re_path(r'^image_codes/(?P<uuid>[\w-]+)/$',views.ImageView.as_view()),

    # 发送短信
    re_path(r'^sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SendSMSView.as_view()),
]