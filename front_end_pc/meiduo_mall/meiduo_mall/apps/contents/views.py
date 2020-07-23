from django.shortcuts import render
from django.views import View
from django.http import JsonResponse

from django.template import loader

from goods.models import SKUImage


# Create your views here.
class CreateView(View):

    def get(self, request):
        # 获取模版对象
        t = loader.get_template('image_satic.html')

        img = SKUImage.objects.get(id=8)
        # data = 'http://10.211.55.35:8888/'+img.image
        data = img.image.url
        # 从数据库中查询了一个图片路径
        data = {
            'url':data
        }
        # 将数据渲染到模版返回html的文本内容
        html_str = t.render(data)
        print(html_str)

        # 将html的文本数据写一个html文件,将html文件保存在前端目录中，
        with open('/Users/august/Desktop/front_end_pc/image_static.html', 'w', encoding='utf-8') as f:
            f.write(html_str)

        return JsonResponse({'code': 0})
