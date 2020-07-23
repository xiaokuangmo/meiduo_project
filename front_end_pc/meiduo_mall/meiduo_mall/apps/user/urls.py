from django.conf.urls import re_path
from . import views
urlpatterns =[
    # 根据设计好的接口文档，匹配相应的路径
    # 用户名的重复判断
    re_path(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$',views.UserNameView.as_view()),
    # 手机号重复判断
    re_path(r'^mobiles/(?P<mobile>\d+)/count/$',views.MobilesView.as_view()),
    # 注册
    re_path(r'^register/$', views.RegisterView.as_view()),
    # 登录
    re_path(r'^login/$', views.LoginView.as_view()),
    # 退出登录
    re_path(r'^logout/$', views.LogOutView.as_view()),
    # 用户中心个人信息获取
    re_path(r'^info/$', views.InfoView.as_view()),
    # 用户中心邮箱保存
    re_path(r'^emails/$', views.EmailView.as_view()),
    # 邮箱验证
    re_path(r'^emails/verification/$', views.EmailVerifyView.as_view()),
    # 用户密码修改
    re_path(r'^password/$', views.CPassWordView.as_view()),


]