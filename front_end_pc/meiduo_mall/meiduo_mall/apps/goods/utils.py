from collections import OrderedDict

from goods.models import GoodsChannel


def get_category():
    # 1、获取频道分组数据 借助OrderedDict()生成一个有序字典
    categories = OrderedDict()
    # 2、order_by指定排序字段，查询的结果会按照指定的字段排序后返回
    channels = GoodsChannel.objects.all().order_by('group_id', 'sequence')
    # 3、循环遍历所有分组，在遍历的时候查询分组下的分类信息
    for channel in channels:
        # 判断分组id是否已经添加，如果未添加则需要加入字典中
        group_id = channel.group_id
        if group_id not in categories:
            categories[group_id] = {
                'channels': [],
                'sub_cats': []
            }
        # 写入一级分类数据, 通过分组表的关联外键category获取关联的商品分类表的一级分类
        # print(group_id)
        cat1 = channel.category
        # print(cat1)
        categories[group_id]['channels'].append(
            {
                'id': cat1.id,
                'name': cat1.name,
                'url': channel.url
            }
        )

        # 根据一级分类查询二级分类信息
        # cat2s=GoodsCategory.objects.filter(parent=cat1)
        cat2s = cat1.subs.all()

        for cat2 in cat2s:
            # 在二级的基础上保存三级分类数据
            cat2.sub_cats = []
            # 更具二级分类对象查询三级分类数据
            cat3s = cat2.subs.all()
            # 通过遍历，将三级分类数据添加到对应的二级分类列表中
            for cat3 in cat3s:
                cat2.sub_cats.append(cat3)
            # 将二级分类添加的有序字典字典中
            categories[group_id]['sub_cats'].append(cat2)

    return categories