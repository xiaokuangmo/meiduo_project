from django.template import loader
from collections import OrderedDict
from goods.models import GoodsChannel, GoodsCategory
from contents.models import ContentCategory, Content

"""
{
    '分组id':{
        'channels':[一级分类数据],
        'sub_cats':[二级分类和三级分类信息]
    }
}


{
    "1":{
        "channels":[
            {"id":1, "name":"手机", "url":"http://shouji.jd.com/"},
            {"id":2, "name":"相机", "url":"http://www.itcast.cn/"}
        ],
        "sub_cats":[
            {
                "id":38, 
                "name":"手机通讯", 
                "sub_cats":[
                    {"id":115, "name":"手机"},
                    {"id":116, "name":"游戏手机"}
                ]
            },
            {
                "id":39, 
                "name":"手机配件", 
                "sub_cats":[
                    {"id":119, "name":"手机壳"},
                    {"id":120, "name":"贴膜"}
                ]
            }
        ]
    },
    "2":{
        "channels":[],
        "sub_cats":[]
    }
}

"""


def create_content_html():
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

    # print(categories)

    # -------------------广告数据---------------------
    # {
    #    '广告分类--手机通讯':[广告内容]
    #      '广告分类--美食生鲜':[广告内容]
    # }

    contents = {}
    # 查询所有的广告类别
    content_cats = ContentCategory.objects.all()
    # 遍历所有的广告类别
    for content_cat in content_cats:
        # 查询分类下的所有数据内容，赋值给对应的广告分类
        contents[content_cat.key] = Content.objects.filter(category=content_cat, status=True).order_by('sequence')


    data={
        'categories':categories,
        'contents':contents
    }

    # 获取模版对象
    t = loader.get_template('index.html')

    # 将数据渲染到模版返回html的文本内容
    html_str = t.render(data)

    # 将html的文本数据写一个html文件,将html文件保存在前端目录中，
    with open('/Users/august/Desktop/front_end_pc/index.html', 'w', encoding='utf-8') as f:
        f.write(html_str)

    # print('执行完成')
