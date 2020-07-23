import json

from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django_redis import get_redis_connection
from datetime import datetime
from goods.models import SKU
from user.models import Address
from orders.models import OrderInfo, OrderGoods
from decimal import Decimal
from django.db import transaction


# Create your views here.
class OrderView(View):
    """
        获取订单信息
    """

    def get(self, request):
        # 1、获取当前用户
        user = request.user
        # 2、根据当前用户获取该用户下的地址信息
        addresses = Address.objects.filter(user=user, is_deleted=False)
        # 3、获取地址后构造返回结果
        address_list = []
        for address in addresses:
            if address.id == user.default_address_id:
                address_list.insert(0,
                                    {
                                        "id": address.id,
                                        "title": address.title,
                                        "receiver": address.receiver,
                                        "province": address.province.name,
                                        "city": address.city.name,
                                        "district": address.district.name,
                                        "place": address.place,
                                        "mobile": address.mobile,
                                    }
                                    )
            else:
                address_list.append(
                    {
                        "id": address.id,
                        "title": address.title,
                        "receiver": address.receiver,
                        "province": address.province.name,
                        "city": address.city.name,
                        "district": address.district.name,
                        "place": address.place,
                        "mobile": address.mobile,
                    }
                )
        # 4、从redis中获取选中的商品信息
        # 4-1 建立链接
        conn = get_redis_connection('carts')
        # 4-2 从集合中获取选中sku_id
        sku_dict = conn.hgetall('cart_%d' % user.id)
        #  获取set集合数据
        selected_sku = conn.smembers('selected_%d' % user.id)
        cart_dict = {}
        # {选中状态商品id：商品数量}
        for sku_id in selected_sku:
            cart_dict[int(sku_id)] = int(sku_dict[sku_id])
        # 5、根据sku_id查询sku表获取sku对象
        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        # 6、构造商品的返回结果
        cart_skus = []
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict.get(sku.id),
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })

        return JsonResponse({
            "code": 0,
            "errmsg": "ok",
            "context": {
                "addresses": address_list,
                "skus": cart_skus,
                "freight": 10,
            }
        })


class OrderCommitView(View):
    """
        保存订单
    """

    def post(self, request):
        # 1、获取前端数据 josn 地址id 支付方式
        data = request.body.decode()
        json_dict = json.loads(data)
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')
        # 2、验证数据
        if not all([address_id, pay_method]):
            return JsonResponse({'code': 400, 'errmsg': '数据不完整'}, status=400)
        # 验证地址是否真的存在
        try:
            address = Address.objects.get(id=address_id)
        except:
            return JsonResponse({'code': 400, 'errmsg': '地址不存在'}, status=400)
        # 验证支付方式
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return JsonResponse({'code': 400, 'errmsg': '支付方式不正确'}, status=400)

        # 3、保存订单基本信息表 datetime.now()获取当前系统时间 strftime()将时间格式为字符串  0000000001
        user = request.user
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + '%09d' % user.id

        with transaction.atomic():
            save_point = transaction.savepoint()
            try:
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal('0'),
                    freight=Decimal('10.00'),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if pay_method == OrderInfo.PAY_METHODS_ENUM[
                        'ALIPAY'] else
                    OrderInfo.ORDER_STATUS_ENUM['UNSEND'])

                # 4、订单商品表
                # 4-1 获取选中的订单商品
                conn = get_redis_connection('carts')
                sku_dict = conn.hgetall('cart_%d' % user.id)
                selected_sku = conn.smembers('selected_%d' % user.id)
                cart_dict = {}
                for sku_id in selected_sku:
                    cart_dict[int(sku_id)] = int(sku_dict[sku_id])
                sku_ids = cart_dict.keys()
                skus = SKU.objects.filter(id__in=sku_ids)
                # 4-2 遍历订单商品
                for sku_id in sku_ids:
                    while True:
                        sku = SKU.objects.get(id=sku_id)
                        # 4-3 遍历商品过程中需要修改库存和销量 sku有库存和销量 spu有总销量
                        old_stock = sku.stock  # 原始库存
                        old_sales = sku.sales  # 原始销量
                        sku_count = cart_dict.get(sku.id)  # 购买的商品数量

                        # 判断一下购买的数量是否大于库存
                        if sku_count > old_stock:
                            return JsonResponse({'code': 400, 'errmsg': '库存不足'}, status=400)

                        # 修改sku库存和销量
                        # sku.stock = old_stock - sku_count
                        # sku.sales = old_sales + sku_count
                        # sku.save()
                        res=SKU.objects.filter(id=sku_id,stock=old_stock).update(sales=old_sales + sku_count,stock=old_stock - sku_count)
                        # 修改spu销量
                        sku.spu.sales += sku_count
                        sku.spu.save()
                        # 4-4 保存订单商品表
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price,

                        )
                        # 4-5 修改订单基本信息表中的总量和总价
                        order.total_count += sku_count
                        order.total_amount += sku_count * sku.price
                        order.save()

                        break
            except:
                transaction.savepoint_rollback(save_point)
        # 5、删除redis中的选中状态的商品，删除购物车数据
        transaction.savepoint_commit(save_point)
        conn.hdel('cart_%s' % user.id, *selected_sku)
        conn.srem('selected_%s' % user.id, *selected_sku)
        return JsonResponse({
            'code': 0,
            'msg': 'ok',
            'order_id': order.order_id
        })
