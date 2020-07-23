from django.conf.urls import re_path
from . import views
urlpatterns =[
    # 根据设计好的接口文档，匹配相应的路径
    # 列表页数据获取
    re_path(r'^list/(?P<category_id>\d+)/skus/$',views.GoodsListView.as_view()),
    # 获取热销商品
    re_path(r'^hot/(?P<category_id>\d+)/$', views.GoodsHotView.as_view()),

    # 商品搜索
    re_path(r'^search/$', views.MySearchView()),

    # 浏览历史记录
    re_path(r'^browse_histories/$', views.GoodsHistory.as_view()),

]