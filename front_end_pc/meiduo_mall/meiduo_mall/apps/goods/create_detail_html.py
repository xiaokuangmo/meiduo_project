from goods.models import SKU, SPUSpecification, SpecificationOption, SKUSpecification
from django.template import loader
from goods.utils import get_category


def create_static_html(sku_id):
    """
        {
            sku:当前的sku商品
            goods:商品的spu数据
            specs:商品规格
        }
    :return:
    """

    # 根据id查询当前sku商品
    sku = SKU.objects.get(id=sku_id)
    print(sku)
    print(sku.default_image.url)
    # 获取spu商品信息
    goods = sku.spu

    # 获取商品品规格
    specs = SPUSpecification.objects.filter(spu=goods)

    # 获取当前sku商品的选项有哪些
    sku_list = []
    sku_spec_options = SKUSpecification.objects.filter(sku=sku)
    for sku_spec_option in sku_spec_options:
        sku_list.append(sku_spec_option.option.id)
    print(sku_list)
    # 获取所有的sku商品选项信息
    # 1、查询sku获取该spu商品下的所有sku商品
    skus = SKU.objects.filter(spu=goods)

    # 2、遍历所有商品  {规格选项:商品id}  {[8,11]:3,[8,12]:4}
    # 比对选项，知道对应商品id
    data_dict = {}
    for sku1 in skus:
        # 获取当前遍历的sku商品的选项
        data_list = []
        sku_spec_options = SKUSpecification.objects.filter(sku=sku1)
        for sku_spec_option in sku_spec_options:
            data_list.append(sku_spec_option.option.id)

        data_dict[tuple(data_list)] = sku1.id
    print(data_dict)
    # 遍历商品规格，确定选项是什么
    for index, spec in enumerate(specs):
        key_list = sku_list[:]
        options = SpecificationOption.objects.filter(spec=spec)
        # 在规格上添加对应的选项信息
        spec.spec_options = options
        # 在选项上添加对应sku_id
        for option in options:
            key_list[index] = option.id
            # print(key_list)
            option.sku_id = data_dict.get(tuple(key_list))
            # print(option)
            # print(option.sku_id)

    # 获取分类导航数据
    categories = get_category()
    data = {
        'sku': sku,
        'goods': goods,
        'specs': specs,
        'categories': categories
    }
    print(data)
    # 渲染数据
    t = loader.get_template('detail.html')

    html_str = t.render(data)
    file_path='/Users/august/Desktop/front_end_pc/goods/%d.html'%sku_id
    # 写入静态文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_str)
    print(file_path)
