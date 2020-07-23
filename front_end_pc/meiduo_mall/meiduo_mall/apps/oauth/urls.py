from django.conf.urls import re_path
from . import views
urlpatterns =[
    # 根据设计好的接口文档，匹配相应的路径
    # QQ登录第一步，构建生成QQ的扫码登录链接
    re_path(r'^qq/authorization/$',views.QQLoginView.as_view()),
    # QQ登录第二步，通过code值获取最终用户的openid值
    # QQ登录第三步，绑定openid
    re_path(r'^oauth_callback/$',views.QQCallBackView.as_view()),


]