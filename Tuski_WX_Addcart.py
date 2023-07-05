#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lz，cj无线组队脚本  BY.Tuski
版本： 1.2
环境变量 活动url： export Tuski_WX_TEAM="活动url"
        线程数： Tuski_WX_TEAM_thread 如未设置默认4线程
        车头数： Tuski_WX_TEAM_capainters 如未设置默认3车头
TG: https://t.me/cooooooCC
脚本会在距离第二天零点前五分钟自动定时，建议签到定时提前5分钟
每天执行三四遍即可  防止断签
建议定时：
禁用就行 Tuski_WX_TEAM.py
"""
import asyncio
import aiohttp, requests
import json, re, os, sys, time
from asgetoken import getoken
from urllib.parse import quote_plus, unquote_plus
from functools import wraps
from Get_cookies import getck
import threading
import telnetlib

def session_manager(async_function):
    @wraps(async_function)
    async def wrapped(*args, **kwargs):
        timeout = aiohttp.ClientTimeout(total=3, connect=3, sock_connect=3, sock_read=3)
        con = aiohttp.TCPConnector(ssl=False)
        session = aiohttp.ClientSession(trust_env=True, timeout=timeout)
        try:
            return await async_function(session=session, *args, **kwargs)
        except aiohttp.ClientError as e:
            raise e
        finally:
            await session.close()

    return wrapped

def with_retries(max_tries, retries_sleep_second):
    def wrapper(function):
        @wraps(function)
        @session_manager
        async def async_wrapped(*args, **kwargs):
            tries = 1
            while tries <= max_tries:
                try:
                    return await function(*args, **kwargs)
                except asyncio.exceptions.TimeoutError as e:
                    print(f"Function: {function.__name__} Caused AiohttpError: {str(e)}, tries: {tries}")
                    tries += 1
                    await asyncio.sleep(retries_sleep_second)
            else:
                raise TimeoutError("Reached aiohttp max tries")

        @wraps(function)
        def wrapped(*args, **kwargs):
            tries = 1
            while tries <= max_tries:
                try:
                    return function(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    print(f"Function: {function.__name__} Caused RequestsError: {str(e)}, tries: {tries}")
                    tries += 1
                    time.sleep(retries_sleep_second)
            else:
                raise TimeoutError("Reached aiohttp max tries")

        if asyncio.iscoroutinefunction(function):
            return async_wrapped
        else:
            return wrapped

    return wrapper

async def get_token(ck):  # 获取token
    try:
        function = 'isvObfuscator'
        body = {"url": f"https://{host}", "id": ""}
        token = await getoken(ck, functionId=function, body=body)
        # print(token)
        return token
    except:
        print('获取token失败')
        return False

async def refreshck(session: aiohttp.ClientSession):  # 获取set_cookie
    url = activityUrl
    headers = {
        'Host': host,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    res = await session.get(url, headers=headers, proxy=proxies)
    if res.status != 200:
        print('IP可能黑了，请更换IP后重试')
    else:
        if "活动已结束" in res:
            print("⛈活动已结束,下次早点来~")
            sys.exit()
        if "活动未开始" in res:
            print("⛈活动未开始~")
            sys.exit()
        if "关注" in res and "加购" not in res:
            activityType = 5
        else:
            activityType = 6
        return activityType


async def shopinfo(session: aiohttp.ClientSession):
    url = f'https://{host}/wxTeam/shopInfo?activityId={activityId}'
    haeders = {
        'Host': host,
        'Connection': 'keep - alive',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': ua,
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Origin': f'https://{host}',
        'Referer': activityUrl,
    }
    res = await session.post(url, headers=haeders, proxy=proxies)
    if res.status == 200:
        text = await res.text()
        res_json = json.loads(text)
        shopName = res_json["data"]["shopName"]
        return shopName
    else:
        return False

async def getSystemConfigForNew(activityType, session: aiohttp.ClientSession):
    url = "https://lzkj-isv.isvjcloud.com/wxCommonInfo/getSystemConfigForNew"
    payload = f'activityId={activityId}&activityType={activityType}'
    headers = {
        'Host': 'lzkj-isv.isvjcloud.com',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://lzkj-isv.isvjcloud.com',
        'User-Agent': ua,
        'Connection': 'keep-alive',
        'Referer': activityUrl,
    }
    await session.post(url, headers=headers, data=payload)


async def getSimpleActInfoVo(session: aiohttp.ClientSession):  # 获取venderId
    url = f'https://{host}/customer/getSimpleActInfoVo'
    haeders = {
        'Host': host,
        'Connection': 'keep - alive',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': ua,
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Origin': f'https://{host}',
        'Referer': activityUrl,
    }
    body = f'activityId={activityId}'
    res = await session.post(url=url, headers=haeders, params=body, proxy=proxies)
    if res.status == 200:
        text = await res.text()
        res_json = json.loads(text)
        global venderId, shopId
        venderId = res_json["data"]["venderId"]
        shopId = res_json["data"]["shopId"]
    else:
        print('getSimpleActInfoVo失败')


async def getping(token, session: aiohttp.ClientSession):  # 获取账号ping值
    url = f'https://{host}/customer/getMyPing?userId={venderId}&token={token}&fromType=APP'
    haeders = {
        'Host': host,
        'Connection': 'keep-alive',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': ua,
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Origin': f'https://{host}',
        'Referer': activityUrl,
    }
    res = await session.post(url, headers=haeders, proxy=proxies)
    if res.status in [200, 201]:
        text = await res.text()
        if "secretPin" in text:
            res_json = json.loads(text)
            secretPin = res_json["data"]["secretPin"]
            secretPin = quote_plus(secretPin)
            '''if '+' in secretPin:
                secretPin = quote_plus(secretPin)
            try:
                pinImg = res_json["data"]["yunMidImageUrl"]
                return secretPin, pinImg
            except Exception as e:'''
            pinImg = ""
            return secretPin, pinImg
        else:
            print("获取ping失败")
            return False
    else:
        print("获取ping失败")
        return False

async def activityContent(secretPin, session: aiohttp.ClientSession):  # 获取活动的信息
    url = f'https://{host}/wxTeam/activityContent'
    data= {'activityId':activityId,'pin':secretPin,'signUuid':''}
    haeders = {
        'Host': host,
        'Connection': 'keep-alive',
        'Accept': 'application/json,text/javascript,*/*;q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': ua,
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Origin': f'https://{host}',
        'Referer': activityUrl,
    }
    res = await session.post(url, headers=haeders,data=data, proxy=proxies)
    if res.status == 200:
        text = await res.text()
        # print(res.status_code)
        if 'data' in text:
            # print(res.text)
            res_json = json.loads(text)
            return res_json
        else:
            return False
    else:
        return False


async def followShop(venderId, pin, activityType,session: aiohttp.ClientSession):
    url = "https://lzkj-isv.isvjcloud.com/wxActionCommon/followShop"
    payload = f"userId={venderId}&activityId={activityId}&buyerNick={quote_plus(pin)}&activityType={activityType}"
    headers = {
        'Host': 'lzkj-isv.isvjcloud.com',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://lzkj-isv.isvjcloud.com',
        'User-Agent': ua,
        'Connection': 'keep-alive',
        'Referer': activityUrl,
    }
    response =await session.post(url, headers=headers, data=payload)
    res = await response.json()
    if res['result']:
        hasFollowShop = res['data']
        return hasFollowShop
    else:
        print(f"⛈{res['errorMessage']}")
        if "店铺会员" in res['errorMessage']:
            return 99


async def addCard(productId, pin, session: aiohttp.ClientSession):
    """加购"""
    url = "https://lzkj-isv.isvjcloud.com/wxCollectionActivity/addCart"
    payload = f"productId={productId}&activityId={activityId}&pin={quote_plus(pin)}"
    headers = {
        'Host': 'lzkj-isv.isvjcloud.com',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://lzkj-isv.isvjcloud.com',
        'User-Agent': ua,
        'Connection': 'keep-alive',
        'Referer': activityUrl,
    }
    response =await session.post(url, headers=headers, data=payload)
    res =await response.json()
    if res['result']:
        hasAddCartSize = res['data']['hasAddCartSize']
        return hasAddCartSize
    else:
        print(f"⛈{res['errorMessage']}")


def collection(productId, pin,session: aiohttp.ClientSession):
    """关注"""
    url = "https://lzkj-isv.isvjcloud.com/wxCollectionActivity/collection"
    payload = f"productId={productId}&activityId={activityId}&pin={quote_plus(pin)}"
    headers = {
        'Host': 'lzkj-isv.isvjcloud.com',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://lzkj-isv.isvjcloud.com',
        'User-Agent': ua,
        'Connection': 'keep-alive',
        'Referer': activityUrl,
    }
    response =await session.post(url, headers=headers, data=payload)
    res = await response.json()
    if res['result']:
        hasCollectionSize = res['data']['hasCollectionSize']
        return hasCollectionSize
    else:
        print(f"⛈{res['errorMessage']}")


async def oneKeyAdd(productIds, pin,session: aiohttp.ClientSession):
    """一键加购"""
    url = "https://lzkj-isv.isvjcloud.com/wxCollectionActivity/oneKeyAddCart"
    payload = f"productIds={productIds}&activityId={activityId}&pin={quote_plus(pin)}"
    headers = {
        'Host': 'lzkj-isv.isvjcloud.com',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://lzkj-isv.isvjcloud.com',
        'User-Agent': ua,
        'Connection': 'keep-alive',
        'Referer': activityUrl,
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    res = response.json()
    if res['result']:
        hasAddCartSize = res['data']['hasAddCartSize']
        return hasAddCartSize
    else:
        print(f"⛈{res['errorMessage']}")

async def getPrize(pin,session: aiohttp.ClientSession):
    url = "https://lzkj-isv.isvjcloud.com/wxCollectionActivity/getPrize"
    payload = f"activityId={activityId}&pin={quote_plus(pin)}"
    headers = {
        'Host': 'lzkj-isv.isvjcloud.com',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://lzkj-isv.isvjcloud.com',
        'User-Agent': ua,
        'Connection': 'keep-alive',
        'Referer': activityUrl,
        'Cookie': f'IsvToken={token};'
    }
    response =await session.post(url, headers=headers, data=payload)
    res =await response.json()
    if res['result']:
        data = res['data']
        if data['drawOk']:
            priceName = data['name']
            return priceName
        else:
            errorMessage = data['errorMessage']
            print(f"⛈{errorMessage}")
            if "不足" in errorMessage:
                sys.exit()
            return errorMessage
    else:
        print(f"⛈{res['errorMessage']}")
        if '奖品已发完' in res['errorMessage']:
            sys.exit()
        return res['errorMessage']

@with_retries(max_tries=2, retries_sleep_second=0.5)
async def get_ACinfo(cookie, session: aiohttp.ClientSession):
    jd_pin = re.findall('pt_pin=(.*?);', cookie)[0]
    token = await get_token(cookie)
    activityType= await refreshck(session)
    await getSystemConfigForNew(activityType,session)
    await getSimpleActInfoVo(session)
    secretPin, pinImg = await getping(token, session)
    res_json = await activityContent(secretPin, session)
    if res_json != False:
        needCollectionSize = res_json['data']['needCollectionSize']
        hasCollectionSize = res_json['data']['hasCollectionSize']
        needFollow = res_json['data']['needFollow']
        hasFollow = res_json['data']['hasFollow']
        cpvos = res_json['data']['cpvos']
        drawInfo = res_json['data']['drawInfo']
        drawOk = drawInfo['drawOk']
        priceName = drawInfo['name']
        oneKeyAddCart = res_json['data']['oneKeyAddCart']
        shopName =await shopinfo(session)
        if cookie == cookies[0]:
            print(f"✅开启{shopName}-加购活动,需关注加购{needCollectionSize}个商品")
            print(f"🎁奖品{priceName}\n")
            msg += f'✅开启{shopName}-加购活动\n📝活动地址{activityUrl}\n🎁奖品{priceName}\n\n'
        if needCollectionSize <= hasCollectionSize:
            print("☃️已完成过加购任务,无法重复进行！")
            continue
        else:
            skuIds = [covo['skuId'] for covo in cpvos if not covo['collection']]
    else:
        print("获取活动信息失败")

async def main():
    pass

if __name__ == '__main__':
    global msg
    ua = 'jdapp;android;10.4.0;10;network/wifi;Mozilla/5.0 (Linux; Android 10; MI 8 Build/QKQ1.190828.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/77.0.3865.120 MQQBrowser/6.2 TBS/045227 Mobile Safari/537.36'
    try:
        activityUrl = os.environ.get("Tuski_WX_TEAM")
    except Exception as e:
        print("获取活动链接失败")
        sys.exit()
    try:
        cookies = getck()
    except Exception as e:
        print("获取ck失败")
        sys.exit()
    try:
        Tuski_WX_Addcart_thread = int(os.environ.get("Tuski_WX_TEAM_thread"))
        print(f"当前并发数：{Tuski_WX_Addcart_thread}")
    except Exception as e:
        print("未设置线程数，默认并发4线程")
        Tuski_WX_TEAM_thread = 3
    try:
        Tuski_WX_TEAM_Proxy = os.environ.get("Tuski_proxy")
        print(f"代理Url：{Tuski_WX_TEAM_Proxy}")
    except Exception as e:
        print("未设置代理")
        Tuski_WX_TEAM_Proxy = None
    print("=" * 60)
    msg = ''
    code = True
    stime = time.time()
    host = re.findall('https?://((?:[\w-]+\.)+\w+(?::\d{1,5})?)', activityUrl)[0]
    activityId = re.findall('[0-9a-z]{32}', activityUrl)[0]
    tasks = []
    asyncio.run(main())
    etime = time.time()
    print(f"本次运行耗费{etime - stime}秒")