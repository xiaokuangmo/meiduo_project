import json

from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
import pickle, base64
from django_redis import get_redis_connection
from goods.models import SKU


# Create your views here.
class CartsView(View):
    """
        购物车操作
    """

    def post(self, request):
        """
            保存购物车
        :param request:
        :return:
        """
        # 1、接受前端数据 sku_id  count json数据
        data = request.body.decode()
        json_dict = json.loads(data)
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        # 2、验证数据
        # 2-1 验证数据的完整性
        if not all([sku_id, count, selected]):
            return JsonResponse({'code': 400, 'errmsg': '数据不完整'}, status=400)
        # 2-2 验证商品是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except:
            return JsonResponse({'code': 400, 'errmsg': '商品不存在'}, status=400)
        # 2-3 验证count值，将所有count转为int类型
        if type(count) != int:
            count = int(count)
        # 2-4 验证selected值，是否为bool类型
        if type(selected) != bool:
            return JsonResponse({'code': 400, 'errmsg': '数据类型不正确'}, status=400)
        # 3、保存数据操作
        # 判断用户是否登录
        user = request.user
        # 3-1 登录用户 保存在redis
        if user.is_authenticated:
            # 建立redis连接
            conn = get_redis_connection('carts')
            # 使用管道
            pl = conn.pipeline()
            # 写入hash的类型的商品id和count数据 hset写入数据，如果数据存在则覆盖原有数据，hincrby方法写入数据是，如果数据field值一样则value进行累加，cart_1:{16:15}  sku_id:16 count :5
            pl.hincrby('cart_%d' % user.id, sku_id, count)
            # 写入set类型的选中状态，如过商品id在集合中说明是选中状态
            if selected:
                pl.sadd('selected_%d' % user.id, sku_id)
            pl.execute()
            # 返回结果
            return JsonResponse({'code': 0, 'msg': 'ok'})
        else:
            # 构造相应对象，进行cookie数据写入
            response = JsonResponse({
                'code': 0,
                'msg': 'ok'
            })
            # 3-2 未登录用户 保存在cookie
            # 先获取cookie，查看是否已经在cookie存储过值
            cart_cookie = request.COOKIES.get('carts')
            # 判断cookie能够获取到
            if cart_cookie:
                # 存在则说明以前存入过加密后的数据，现在需要进行解密
                data_dict = pickle.loads(base64.b64decode(cart_cookie))
            else:
                data_dict = {}

            # 判断商品id是否在data_dict字典中，存在则说明该商品已经存储过，那么商品就需要进行累加
            if sku_id in data_dict:
                count += data_dict[sku_id]['count']

            # 将数据写入data_dict字典
            data_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            # 对data_dict字典进行加密
            carts = base64.b64encode(pickle.dumps(data_dict)).decode()
            # 将加密数据写入cookies
            response.set_cookie('carts', carts)
            # 4-返回结果
            return response

    def get(self, request):
        """
            获取购物车数据
        :param request:
        :return:
        """

        # 1、判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 2、登录用从redis中获取数据
            # 2-1 建立redis连接
            conn = get_redis_connection('carts')
            # 2-2 获取hash数据
            sku_dict = conn.hgetall('cart_%d' % user.id)
            # 2-3 获取set集合数据
            selected_sku = conn.smembers('selected_%d' % user.id)
            # 2-4 构造和cookie一样的数据结构
            cart_dict = {}
            for sku_id, count in sku_dict.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in selected_sku
                }
        else:
            # 3、未登录用户 从cookie中获取数据
            # 先获取cookie，查看是否已经在cookie存储过值
            cart_cookie = request.COOKIES.get('carts')
            # 判断cookie能够获取到
            if cart_cookie:
                # 存在则说明以前存入过加密后的数据，现在需要进行解密
                cart_dict = pickle.loads(base64.b64decode(cart_cookie))
            else:
                cart_dict = {}

        # 4、返回数据
        # 4-1 根据sku——id，先获取sku商品对象
        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        # 4-2 遍商品对象，构造相应数据内容
        cart_skus = []
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict.get(sku.id).get('count'),
                'selected': cart_dict.get(sku.id).get('selected'),
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * cart_dict.get(sku.id).get('count'),
            })

        return JsonResponse({
            'code': 0,
            'msg': 'ok',
            'cart_skus': cart_skus
        })

    def put(self, request):
        """
            更新购物车
        :param request:
        :return:
        """
        # 1、接受前端数据 sku_id  count json数据
        data = request.body.decode()
        json_dict = json.loads(data)
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        # 2、验证数据
        # 2-1 验证数据的完整性
        # ------------区别----------------
        if not all([sku_id, count]):
            return JsonResponse({'code': 400, 'errmsg': '数据不完整'}, status=400)
        # ------------区别----------------
        # 2-2 验证商品是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except:
            return JsonResponse({'code': 400, 'errmsg': '商品不存在'}, status=400)
        # 2-3 验证count值，将所有count转为int类型
        if type(count) != int:
            count = int(count)
        # 2-4 验证selected值，是否为bool类型
        if type(selected) != bool:
            return JsonResponse({'code': 400, 'errmsg': '数据类型不正确'}, status=400)
        # 3、修改数据操作
        # 判断用户是否登录
        user = request.user
        # 3-1 登录用户  更新redis中的数据
        if user.is_authenticated:
            # 建立redis连接
            conn = get_redis_connection('carts')
            # 使用管道
            pl = conn.pipeline()
            # 写入hash的类型的商品id和count数据 hset写入数据，如果数据存在则覆盖原有数据，hincrby方法写入数据是，如果数据field值一样则value进行累加，cart_1:{16:15}  sku_id:16 count :5
            # ------------区别----------------
            pl.hset('cart_%d' % user.id, sku_id, count)
            # 写入set类型的选中状态，如过商品id在集合中说明是选中状态
            if selected:
                pl.sadd('selected_%d' % user.id, sku_id)
            else:
                pl.srem('selected_%d' % user.id, sku_id)
            # ------------区别----------------
            pl.execute()
            # 返回结果
            return JsonResponse({'code': 0, 'msg': 'ok', "cart_sku": {
                'id': sku_id,
                'count': count,
                'selected': selected
            }})
        else:
            # 构造相应对象，进行cookie数据写入
            response = JsonResponse({
                'code': 0,
                'msg': 'ok',
                "cart_sku": {
                    'id': sku_id,
                    'count': count,
                    'selected': selected
                }
            })
            # 3-2 未登录用户 保存在cookie
            # 先获取cookie，查看是否已经在cookie存储过值
            cart_cookie = request.COOKIES.get('carts')
            # 判断cookie能够获取到
            if cart_cookie:
                # 存在则说明以前存入过加密后的数据，现在需要进行解密
                data_dict = pickle.loads(base64.b64decode(cart_cookie))
            else:
                data_dict = {}
            # ------------区别----------------
            # 将数据写入data_dict字典
            data_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            # 对data_dict字典进行加密
            carts = base64.b64encode(pickle.dumps(data_dict)).decode()
            # 将加密数据写入cookies
            response.set_cookie('carts', carts)
            # 4-返回结果
            return response

    def delete(self, request):
        """
            删除购物车
        :param request:
        :return:
        """
        # 1、接受前端数据 sku_id  count json数据
        data = request.body.decode()
        json_dict = json.loads(data)
        sku_id = json_dict.get('sku_id')

        # 2、验证数据
        # 2-2 验证商品是否存在
        # ------------区别----------------
        try:
            sku = SKU.objects.get(id=sku_id)
        except:
            return JsonResponse({'code': 400, 'errmsg': '商品不存在'}, status=400)
        # ------------区别----------------
        # 3、修改数据操作
        # 判断用户是否登录
        user = request.user
        # 3-1 登录用户  删除redis中的数据
        if user.is_authenticated:
            # 建立redis连接
            conn = get_redis_connection('carts')
            # 使用管道
            pl = conn.pipeline()
            # ------------区别----------------
            # 删除hash数据
            pl.hdel('cart_%d' % user.id, sku_id)
            # 删除set类型的选中状态，如过商品id在集合中说明是选中状态
            pl.srem('selected_%d' % user.id, sku_id)
            # ------------区别----------------
            pl.execute()
            # 返回结果
            return JsonResponse({'code': 0, 'msg': 'ok'})
        else:
            # 构造相应对象，进行cookie数据写入
            response = JsonResponse({
                'code': 0,
                'msg': 'ok',
            })
            # 3-2 未登录用户 保存在cookie
            # 先获取cookie，查看是否已经在cookie存储过值
            cart_cookie = request.COOKIES.get('carts')
            # 判断cookie能够获取到
            if cart_cookie:
                # 存在则说明以前存入过加密后的数据，现在需要进行解密
                data_dict = pickle.loads(base64.b64decode(cart_cookie))

                # -------- 区别-----------
                # 删除data_dict字典的数据
                if sku_id in data_dict:
                    del data_dict[sku_id]
                # -------- 区别-----------

                # 对data_dict字典进行加密
                carts = base64.b64encode(pickle.dumps(data_dict)).decode()
                # 将加密数据写入cookies
                response.set_cookie('carts', carts)
            # 4-返回结果
            return response


class CartsSelectionView(View):

    def put(self, request):
        """
            全选状态的修改
        :param request:
        :return:
        """
        # 1、接受前端数据 selected数据
        data = request.body.decode()
        json_dict = json.loads(data)
        selected = json_dict.get('selected', True)

        # 2、验证数据
        # ------------区别----------------
        # 2 验证selected值，是否为bool类型
        if type(selected) != bool:
            return JsonResponse({'code': 400, 'errmsg': '数据类型不正确'}, status=400)
        # ------------区别----------------
        # 3、修改数据操作
        # 判断用户是否登录
        user = request.user
        # 3-1 登录用户  更新redis中的数据
        if user.is_authenticated:
            # 建立redis连接
            conn = get_redis_connection('carts')
            # 使用管道
            pl = conn.pipeline()
            # ------------区别----------------
            # 从hash数据中获取所有的sku_id
            sku_dict = conn.hgetall('cart_%d' % user.id)
            sku_ids = sku_dict.keys()
            # 更新所有商品的选中状态[1,2,3]  1,2,3
            if selected:
                pl.sadd('selected_%d' % user.id, *sku_ids)
            else:
                pl.srem('selected_%d' % user.id, *sku_ids)
            # ------------区别----------------
            pl.execute()
            # 返回结果
            return JsonResponse({'code': 0, 'msg': 'ok'})
        else:
            # 构造相应对象，进行cookie数据写入
            response = JsonResponse({
                'code': 0,
                'msg': 'ok',
            })
            # 3-2 未登录用户 保存在cookie
            # 先获取cookie，查看是否已经在cookie存储过值
            cart_cookie = request.COOKIES.get('carts')
            # 判断cookie能够获取到
            if cart_cookie:
                # 存在则说明以前存入过加密后的数据，现在需要进行解密
                data_dict = pickle.loads(base64.b64decode(cart_cookie))
                # ------------区别----------------
                # 修改data_dict字典所有的选中状态
                for sku_id in data_dict.keys():
                    data_dict[sku_id]['selected'] = selected
                # ------------区别----------------
                # 对data_dict字典进行加密
                carts = base64.b64encode(pickle.dumps(data_dict)).decode()
                # 将加密数据写入cookies
                response.set_cookie('carts', carts)
            # 4-返回结果
            return response


class CartsSimpleView(View):
    """
        获取简单数据
    """

    def get(self,request):

        # 1、判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 2、登录用从redis中获取数据
            # 2-1 建立redis连接
            conn = get_redis_connection('carts')
            # 2-2 获取hash数据
            sku_dict = conn.hgetall('cart_%d' % user.id)
            # 2-3 获取set集合数据
            selected_sku = conn.smembers('selected_%d' % user.id)
            # 2-4 构造和cookie一样的数据结构
            cart_dict = {}
            for sku_id, count in sku_dict.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in selected_sku
                }
        else:
            # 3、未登录用户 从cookie中获取数据
            # 先获取cookie，查看是否已经在cookie存储过值
            cart_cookie = request.COOKIES.get('carts')
            # 判断cookie能够获取到
            if cart_cookie:
                # 存在则说明以前存入过加密后的数据，现在需要进行解密
                cart_dict = pickle.loads(base64.b64decode(cart_cookie))
            else:
                cart_dict = {}

        # 4、返回数据
        # 4-1 根据sku——id，先获取sku商品对象
        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        # 4-2 遍商品对象，构造相应数据内容
        cart_skus = []
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict.get(sku.id).get('count'),
                'default_image_url': sku.default_image.url,
            })

        return JsonResponse({
            'code': 0,
            'msg': 'ok',
            'cart_skus': cart_skus
        })