import json
import re

from django.core.cache import cache
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from addresses.models import Area

from user.models import Address


# Create your views here.
class AreasView(View):
    """
        省市区数据获取
    """

    def get(self, request):
        """
            获取省数据
        :param request:
        :return:
        """
        # 每次获取省数据时都会区查询mysql数据，这时可以将省市区数据缓存到redis，这可以减轻myslq数据的查询压力
        data_list = cache.get('data_list')

        if data_list is None:
            # 1、查询所有省的数据
            datas = Area.objects.filter(parent=None)
            # 2、返回省的数据
            data_list = []
            for data in datas:
                data_list.append(
                    {
                        'id': data.id,
                        'name': data.name
                    }
                )
            # 3、缓存
            cache.set('data_list', data_list)
        return JsonResponse(
            {
                'code': 0,
                'msg': 'ok',
                'province_list': data_list
            }
        )


class AreasesView(View):
    """
        获取市区信息
    """

    def get(self, request, pk):
        """

        :param request:
        :param pk:  接收是省的id值
        :return:
        """
        # 1、根据省或市的id查询省或市信息
        province = Area.objects.get(id=pk)
        # 2、根据省或市查询下一级市或区县信息
        subs = Area.objects.filter(parent_id=pk)
        # 3、将查询到的数据进行返回
        # 遍历所有市或区县信息
        city_list = []
        for sub in subs:
            city_list.append({
                'id': sub.id,
                'name': sub.name
            })

        return JsonResponse(
            {
                'code': 0,
                'msg': 'ok',
                'sub_data': {
                    'id': province.id,
                    'name': province.name,
                    'subs': city_list
                }
            }
        )


class AddressesView(View):
    """
        地址管理
    """

    def post(self, request):
        """
            保存地址
        :param request:
        :return:
        """
        # 1、获取前端数据 json
        # receiver	string	是	收货人
        # province_id	string	是	省份ID
        # city_id	string	是	城市ID
        # district_id	string	是	区县ID
        # place	string	是	收货地址
        # mobile	string	是	手机号
        # tel	string	否	固定电话
        # email	string	否	邮箱
        # 获取登录用户
        user = request.user
        data = request.body.decode()
        data_dict = json.loads(data)
        receiver = data_dict.get('receiver')
        province_id = data_dict.get('province_id')
        city_id = data_dict.get('city_id')
        district_id = data_dict.get('district_id')
        place = data_dict.get('place')
        mobile = data_dict.get('mobile')
        tel = data_dict.get('tel')
        email = data_dict.get('email')
        # 2、验证数据
        # 验证数据的完整性
        if not all([province_id, receiver, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 400, 'errmsg': '缺少数据'}, status=400)

        # 验证手机号格式
        if not re.match(r'1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400, 'errmsg': '数据错误'}, status=400)

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数email有误'})

        # 3、保存数据
        address = Address.objects.create(user=user,
                                         title=receiver,
                                         receiver=receiver,
                                         province_id=province_id,
                                         city_id=city_id,
                                         district_id=district_id,
                                         place=place,
                                         mobile=mobile,
                                         tel=tel,
                                         email=email
                                         )
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email,
            'length': 20
        }
        # 4、返回结果
        return JsonResponse(
            {
                'code': 0,
                'errmsg': '新增地址成功',
                'address': address_dict
            }
        )

    def get(self, request):
        """
            获取收货地址
        :param request:
        :return:
        """
        # 1、查询当前登录用户的地址
        user = request.user
        addresses = Address.objects.filter(user=user, is_deleted=False)

        # 2、遍历地址信息进行返回
        address_list = []
        for address in addresses:
            if address.id == user.default_address_id:
                address_list.insert(0,
                                    {
                                        "id": address.id,
                                        "title": address.title,
                                        "receiver": address.receiver,
                                        "province": address.province.name,
                                        "city": address.city.name,
                                        "district": address.district.name,
                                        "place": address.place,
                                        "mobile": address.mobile,
                                        "tel": address.tel,
                                        "email": address.email
                                    }
                                    )
            else:
                address_list.append(
                    {
                        "id": address.id,
                        "title": address.title,
                        "receiver": address.receiver,
                        "province": address.province.name,
                        "city": address.city.name,
                        "district": address.district.name,
                        "place": address.place,
                        "mobile": address.mobile,
                        "tel": address.tel,
                        "email": address.email
                    }
                )

        return JsonResponse(
            {
                "code": 0,
                "errmsg": "ok",
                'default_address_id': user.default_address_id,
                "addresses": address_list
            }
        )

    def put(self, request, address_id):
        """
            更新地址
        :param request:
        :return:
        """
        # 1、获取前端数据 json
        # 获取登录用户
        user = request.user
        data = request.body.decode()
        # 将前端传递json数据转化为字典
        data_dict = json.loads(data)

        receiver = data_dict.get('receiver')
        province_id = data_dict.get('province_id')
        city_id = data_dict.get('city_id')
        district_id = data_dict.get('district_id')
        place = data_dict.get('place')
        mobile = data_dict.get('mobile')
        tel = data_dict.get('tel')
        email = data_dict.get('email')

        # 2、验证数据

        # 验证手机号格式
        if mobile:
            if not re.match(r'1[3-9]\d{9}$', mobile):
                return JsonResponse({'code': 400, 'errmsg': '数据错误'}, status=400)

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数email有误'})

        # 3、更新数据  data={'name':'python','age':18}  **data name=pyhton,age=18
        del data_dict['province']
        del data_dict['city']
        del data_dict['district']
        del data_dict['id']
        Address.objects.filter(user=user, id=address_id).update(**data_dict)
        # 查询获取更新后地址对象
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }
        # 4、返回结果
        return JsonResponse(
            {
                'code': 0,
                'errmsg': '新增地址成功',
                'address': address_dict
            }
        )

    def delete(self, request, address_id):

        # 1、查询要删除的地址对象 删除
        # 物理删除，会直接将数据从数据库中清除
        # Address.objects.filter(id=address_id).delete()
        # 逻辑删除，更新逻辑删除字段，并不会从数据中删除数据
        res = Address.objects.filter(id=address_id).update(is_deleted=True)
        if res == 0:
            return JsonResponse({'code': 400, 'msg': '删除失败'}, status=400)
        # 返回结果
        return JsonResponse({'code': 0, 'msg': 'ok'})


class AddressesDefaultView(View):
    """
        设置默认地址，将用户表的默认地址字段更新
    """

    def put(self, request, address_id):
        # 1、获取当前用户
        user = request.user
        # 2、更新默认地址字段
        user.default_address_id = address_id
        user.save()
        return JsonResponse({'code': 0, 'msg': 'ok'})


class AddressesTitleView(View):
    """
        设置地址标题
    """

    def put(self, request, address_id):

        # 1、根据地址id查询要更新的地址对象，get方法查询不到会抛出异常
        try:
            address = Address.objects.get(id=address_id)
        except:
            return JsonResponse({'code': 400, 'errmsg': '地址不存在'}, status=400)
        # 2、更新地址标题
        # 获取title json
        data = request.body.decode()
        data_dict = json.loads(data)
        title = data_dict.get('title')
        address.title = title
        address.save()
        # 3、返回结果
        return JsonResponse({'code': 0, 'msg': 'ok'})
