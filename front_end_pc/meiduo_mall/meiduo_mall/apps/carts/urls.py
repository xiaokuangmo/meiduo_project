from django.conf.urls import re_path

from . import views
urlpatterns =[
    # 根据设计好的接口文档，匹配相应的路径

    re_path(r'^carts/$',views.CartsView.as_view()),
    # 全选状态修改
    re_path(r'^carts/selection/$',views.CartsSelectionView.as_view()),
    # 简单购物车数据
    re_path(r'^carts/simple/$',views.CartsSimpleView.as_view())
]