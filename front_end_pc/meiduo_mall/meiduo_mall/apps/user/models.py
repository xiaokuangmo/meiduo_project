from django.db import models

from django.contrib.auth.models import AbstractUser

# Create your models here.

# class BookInfo(models.Model)
# 继承Django认证系统自带的用户表
from meiduo_mall.utils.BaseModel import BaseModel


class User(AbstractUser):
    # 原有的用户没有手机号字段unique指定唯一值
    mobile = models.CharField(max_length=11, unique=True)
    # 新增 email_active 字段
    # 用于记录邮箱是否激活, 默认为 False: 未激活
    email_active = models.BooleanField(default=False,
                                       verbose_name='邮箱验证状态')

    # 新增
    default_address = models.ForeignKey('Address',related_name='users',null=True,blank=True,on_delete=models.SET_NULL,verbose_name='默认地址')

    class Meta:
        db_table = 'tb_user'

    def __str__(self):
        # 打印类对象时，显示返回的结果内容
        return self.username


# 增加地址的模型类, 放到User模型类的下方:
class Address(BaseModel):
    """
    用户地址
    """
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='addresses',
                             verbose_name='用户')

    province = models.ForeignKey('addresses.Area',
                                 on_delete=models.PROTECT,
                                 related_name='province_addresses',
                                 verbose_name='省')

    city = models.ForeignKey('addresses.Area',
                             on_delete=models.PROTECT,
                             related_name='city_addresses',
                             verbose_name='市')

    district = models.ForeignKey('addresses.Area',
                                 on_delete=models.PROTECT,
                                 related_name='district_addresses',
                                 verbose_name='区')

    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20,
                           null=True,
                           blank=True,
                           default='',
                           verbose_name='固定电话')

    email = models.CharField(max_length=30,
                             null=True,
                             blank=True,
                             default='',
                             verbose_name='电子邮箱')

    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_time'] # 指定查询数据后的排序
