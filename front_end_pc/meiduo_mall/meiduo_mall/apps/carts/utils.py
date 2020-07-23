import base64
import pickle

from django_redis import get_redis_connection


def cart_goods(request, response, user):
    """
        合并购物车
    :return:
    """

    # 1、获取cookie数据
    cart_cookie = request.COOKIES.get('carts')
    if not cart_cookie:
        return response
    # 2、现在需要进行解密
    data_dict = pickle.loads(base64.b64decode(cart_cookie))
    # 3、判断解密后的字典数据是否为空 {}  {sku_id:{count:10,selected:True}}
    if data_dict is None:
        response.delete_cookie('carts')
        return response

    # 4、构造存入redis中的数据结构
    # 4-1 构造hash数据 key:{sku_id:count}
    sku_dict = {}
    # 4-2 构造集合数据
    # 选中状态的list
    sku_selected = []
    # 为选中状态的list
    sku_selected_none = []
    for sku_id, count_dict in data_dict.items():
        sku_dict[sku_id] = count_dict['count']
        if count_dict['selected']:
            # 当前商品是选中状态，添加到sku_selected列表中
            sku_selected.append(sku_id)
        else:
            sku_selected_none.append(sku_id)

    # 5、连接redis，写入构造好的数据
    conn = get_redis_connection('carts')
    pl = conn.pipeline()
    # 写入hash类型
    pl.hmset('cart_%d' % user.id, sku_dict)
    # 写入集合
    if sku_selected:
        pl.sadd('selected_%d' % user.id, *sku_selected)
    # 删除集合数据
    if sku_selected_none:
        pl.srem('selected_%d' % user.id, *sku_selected_none)
    pl.execute()

    # 6、删除cookie
    response.delete_cookie('carts')

    return response
