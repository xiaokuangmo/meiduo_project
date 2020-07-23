from django.conf.urls import re_path

from . import views
urlpatterns =[
    # 根据设计好的接口文档，匹配相应的路径
    re_path(r'^orders/settlement/$',views.OrderView.as_view()),
    re_path(r'^orders/commit/$',views.OrderCommitView.as_view())
]