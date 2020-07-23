from django.http import JsonResponse


def usermiddleware(get_response):
    """
        使用中间件完成登录状态判断
    :param get_response:接受的时视图方法
    :return:
    """

    def warpper(request, *args, **kwargs):
        # 视图调用之前先判断用户是否登录过，指定相应的请求
        url_list = ['/info/', '/orders/settlement/']
        if request.path in url_list:
            # 请求路径在这个列表中需要进行登录状态的判断
            if not request.user.is_authenticated:
                return JsonResponse({'code': 401, 'errmsg': '用户未登录'}, status=401)

        response = get_response(request, *args, **kwargs)

        return response

    return warpper
