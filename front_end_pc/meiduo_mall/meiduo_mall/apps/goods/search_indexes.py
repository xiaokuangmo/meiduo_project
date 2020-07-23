from haystack import indexes

from goods.models import SKU
class SKUIndex(indexes.SearchIndex,indexes.Indexable):

    # 指定索引字段
    # 指定模型字段后text的数据由指定的字段数据构成
    # text= （id name caption）
    # text= '6 Apple iPhone 8 Plus (A1864) 256GB 深空灰色 移动联通电信4G手机 选【移动优惠购】新机配新卡，198优质靓号，流量不限量！
    text = indexes.CharField(document=True,use_template=True)

    # 指定创建索引的数据
    def get_model(self):
        return SKU

    # 指定表中那些数据需要建立索引
    def index_queryset(self, using=None):
        return self.get_model().objects.filter(is_launched=True)