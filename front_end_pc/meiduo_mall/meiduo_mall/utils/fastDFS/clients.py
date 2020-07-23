# from fdfs_client.client import Fdfs_client
#
# c = Fdfs_client('./client.conf')
#
# res = c.upload_by_filename('./94.png')
#
# print(res)
# 导入Django的模版文件方法
from django.template import loader

# 获取模版文件对象
def create_html():
    t=loader.get_template('image_satic.html')
    # 从数据库中查询了一个图片路径
    data={
        'url':'http://10.211.55.35:8888/group1/M00/00/00/CtM3I16_lLeAIwkeAAkIkdXkeHE798.png'
    }
    html_str=t.render(data)
    print(html_str)

create_html()