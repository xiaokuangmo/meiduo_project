from django.conf.urls import re_path
from . import views
urlpatterns =[
    # 根据设计好的接口文档，匹配相应的路径
    re_path(r'^areas/$',views.AreasView.as_view()),
    # 获取市区的信息
    re_path(r'^areas/(?P<pk>[1-9]\d+)/$',views.AreasesView.as_view()),

    # 地址管理 保存地址
    re_path(r'^addresses/create/$', views.AddressesView.as_view()),
    # 获取地址
    re_path(r'^addresses/$', views.AddressesView.as_view()),
    # 更新地址\删除地址
    re_path(r'^addresses/(?P<address_id>\d+)/$', views.AddressesView.as_view()),
    # 设置默认地址
    re_path(r'^addresses/(?P<address_id>\d+)/default/$', views.AddressesDefaultView.as_view()),

    # 设置标题
    re_path(r'^addresses/(?P<address_id>\d+)/title/$', views.AddressesTitleView.as_view()),




]