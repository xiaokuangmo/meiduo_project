import json

from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from goods.models import SKU, GoodsCategory

from haystack.views import SearchView
# 导入Django处理分页的方法类
from django.core.paginator import Paginator
from django_redis import get_redis_connection

from goods.models import SKU


# Create your views here.
class GoodsListView(View):
    """
        列表页数据获取
    """

    def get(self, request, category_id):
        # 1、获取数据
        # page	string	是	当前页码 ( 查询字符串参数 )
        # page_size	string	是	每页数量 ( 查询字符串参数 )
        # ordering	string	是	排序方式 ( 查询字符串参数 )

        page = request.GET.get('page')
        page_size = request.GET.get('page_size')
        ordering = request.GET.get('ordering')
        # 2、查询商品表
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by(ordering)
        # 3、分页处理 第一参数是要分页的数据对象，第二个参数 每页数量
        paginator = Paginator(skus, page_size)
        # 获取分页后的数据 参数 传递的是页数
        sku_page = paginator.page(page)
        # 获取总页数
        count = paginator.num_pages

        data_list = []
        for data in sku_page:
            data_list.append({
                'id': data.id,
                'price': data.price,
                'name': data.name,
                'default_image_url': data.default_image.url
            })
        # 面包屑导航数据返回
        breadcrumb = {
            'cat1': '',
            'cat2': '',
            'cat3': ''
        }
        cat = GoodsCategory.objects.get(id=category_id)
        if cat.parent is None:
            # 是空值说明一级分类
            breadcrumb['cat1'] = cat.name

        elif cat.parent.parent is None:
            # 说明是二级分类
            breadcrumb['cat1'] = cat.parent.name
            breadcrumb['cat2'] = cat.name

        else:
            breadcrumb['cat1'] = cat.parent.parent.name
            breadcrumb['cat2'] = cat.parent.name
            breadcrumb['cat3'] = cat.name
        # 4、返回结果
        return JsonResponse({
            'code': 0,
            'msg': 'ok',
            'count': count,
            'list': data_list,
            'breadcrumb': breadcrumb
        })


class GoodsHotView(View):
    """
        热销商品获取
    """

    def get(self, request, category_id):
        # 1、获取前端数据 （分类id）
        # 2、根据分类id查询该分类下的热销商品 （查询完成后需要按照销量字段排序），选择前三位的商品展示  -sales 减号表示降序 从大到小排序
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]
        # 遍历商品的字段
        data_list = []
        for data in skus:
            data_list.append({
                'id': data.id,
                'price': data.price,
                'name': data.name,
                'default_image_url': data.default_image.url
            })
        # 3、返回结果
        return JsonResponse({
            'code': 0,
            'msg': 'ok',
            'hot_skus': data_list
        })


class MySearchView(SearchView):

    # 使用SearchView的方法是不需要在进行请求方式的匹配
    # 我们需要对它返回的结果方法进行重写
    def create_response(self):
        # 获取前端传递的页数 原生方法中使用self.request获取搜索内容
        page = self.request.GET.get('page')
        # 获取检索到的商品数据
        context = self.get_context()
        # 构建返回结构数据
        data_list = []
        for sku in context['page'].object_list:
            data_list.append({
                'id': sku.object.id,
                'name': sku.object.name,
                'price': sku.object.price,
                'default_image_url': sku.object.default_image.url,
                'searchkey': context.get('query'),
                'page_size': context['page'].paginator.num_pages,
                'count': context['page'].paginator.count
            })

        # 返回结果

        return JsonResponse(data_list, safe=False)


class GoodsHistory(View):
    """
        浏览历史记录
    """

    def post(self, request):
        # 1、获取前端数据
        data = request.body.decode()
        data_dict = json.loads(data)
        sku_id = data_dict.get('sku_id')
        # 2、连接redis写入数据
        # 2-1 连接reids
        conn = get_redis_connection('history')
        # 2-2去重操作
        id = request.user.id
        conn.lrem('history_%d' % id, 0, sku_id)
        # 2-3 写入
        conn.lpush('history_%d' % id, sku_id)
        # 2-4 控制数量
        conn.ltrim('history_%d' % id, 0, 5)
        # 3、返回结果
        return JsonResponse({
            'code': 0,
            'msg': 'ok'
        })

    def get(self, request):
        # 1、查询redis数据库
        # 1-1 连接reids
        conn = get_redis_connection('history')
        id = request.user.id
        sku_ids = conn.lrange('history_%d' % id, 0, 100)
        # 2、遍历查询sku表
        # sku_list=[]
        # for sku_id in sku_ids:
        #     sku_list.append(SKU.objects.get(id=int(sku_id)))
        # 范围查询，在sku_id列表内的数据都会返回
        skus = SKU.objects.filter(id__in=sku_ids)

        # 3、构建返回结果
        sku_list = []
        for sku in skus:
            sku_list.append({
                'id':sku.id,
                'name':sku.name,
                'price':sku.price,
                'default_image_url':sku.default_image.url
            })

        return JsonResponse({
            'code': 0,
            'msg': 'ok',
            'skus':sku_list
        })
