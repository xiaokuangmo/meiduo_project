from django.template import loader
import sys
sys.path.insert(0,'/Users/august/Desktop/Python/meiduo/meiduo_mall/meiduo_mall/apps')
from celery_tasks.main import celery_app
from goods.create_detail_html import create_static_html

@celery_app.task(name='create_static_detail_html')
def create_static_detail_html(sku_id):
    create_static_html(sku_id)

