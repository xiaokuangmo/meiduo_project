from django.template import loader
import sys
sys.path.insert(0,'/Users/august/Desktop/Python/meiduo/meiduo_mall')
from celery_tasks.main import celery_app
# from celery_tasks.yuntongxun.ccp_sms import CCP
from meiduo_mall.libs.yuntongxun.ccp_sms import CCP

@celery_app.task(name='send_sms')  # 指定异步任务名
def send_sms(mobile, sms_code):
    data = CCP().send_template_sms(mobile, [sms_code, 5], 1)
    # print(data)
    return data
