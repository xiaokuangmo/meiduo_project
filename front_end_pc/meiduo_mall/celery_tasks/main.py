from celery import Celery
import sys
# sys.path.insert(0,'/Users/august/Desktop/Python/meiduo/meiduo_mall')
# print(sys.path)
celery_app = Celery('meiduo')
# 异步任务中用到Django的方法，需要将Django的配置文件导入进来
import os
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo_mall.settings.dev'
# 启动Django服务
import django
django.setup()
# 将刚刚的 config 配置给 celery
# 里面的参数为我们创建的 config 配置文件:
celery_app.config_from_object('celery_tasks.config')

# 定义完任务方法后需要添加到任务队列
celery_app.autodiscover_tasks(['celery_tasks.sms','celery_tasks.emails','celery_tasks.create_static_html'])
