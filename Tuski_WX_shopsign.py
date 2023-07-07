#!/usr/bin/env python3
# -- coding: utf-8 --**

"""
lz，cj无线签到脚本  BY.Tuski
版本： 3.0
环境变量 活动url： export Tuski_WX_TEAM="活动url"
        线程数： Tuski_WX_TEAM_thread 如未设置默认4线程
        车头数： Tuski_WX_TEAM_capainters 如未设置默认3车头
TG: https://t.me/cooooooCC
crone:   2 45 23 * * *
new Env('Tuski_无线签到');
Tuski_WX_shopsign.py
"""

import asyncio
import datetime
import os.path
import sys
import copy
import aiofiles
import aiohttp, requests
import json, re, time
from time import localtime
from asgetoken import getoken
from urllib.parse import quote_plus, unquote_plus
from functools import wraps
import threading
import telnetlib
from Get_cookies import getck
from fake_useragent import UserAgent
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sendNotify import send
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor


award_sign=[]
logging.basicConfig(level=logging.WARNING, format='%(message)s')
logging.getLogger('apscheduler').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

job_defaults = {
    'coalesce': False,
    'max_instances': 40
}
scheduler = AsyncIOScheduler(
    job_defaults=job_defaults,
    timezone='Asia/Shanghai'
)

async def cache_write():
    for i in sign_data["data"]:
        if int(time.time()) > i['endTime']:
            sign_data["data"].remove(i)
            logger.warning(f'{i} 失效移除')
        if i['signed_days'] >= int(i['gifday'][-1]):
            sign_data["data"].remove(i)
            logger.warning(f'{i} 签完移除')
    async with aiofiles.open("cache/wx_sign_data.json", "w", encoding="utf-8") as fp:
        await fp.write(json.dumps(sign_data, indent=4, ensure_ascii=False))


def read_cache():
    if os.path.exists('cache/wx_sign_data.json'):
        with open("cache/wx_sign_data.json", "r", encoding="utf-8") as fp:
            sign_data = json.load(fp)
        return sign_data
    else:
        os.mkdir('cache')
        with open("cache/wx_sign_data.json", "w", encoding="utf-8") as f:
            sign_data = {'data': []}
            f.write(json.dumps(sign_data))
            return sign_data

def session_manager(async_function):
    @wraps(async_function)
    async def wrapped(*args, **kwargs):
        timeout = aiohttp.ClientTimeout(total=3, connect=3, sock_connect=3, sock_read=3)
        con = aiohttp.TCPConnector(ssl=False)
        session = aiohttp.ClientSession(trust_env=True, timeout=timeout, connector=con)
        try:
            return await async_function(session=session, *args, **kwargs)
        except aiohttp.ClientError as e:
            logger.warning(e)
            pass
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
                    logger.warning(f"Function: {function.__name__} Caused AiohttpError: {str(e)}, tries: {tries}")
                    tries += 1
                    await asyncio.sleep(retries_sleep_second)
            else:
                logger.warning('重试超上限')
                pass

        @wraps(function)
        def wrapped(*args, **kwargs):
            tries = 1
            while tries <= max_tries:
                try:
                    return function(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Function: {function.__name__} Caused RequestsError: {str(e)}, tries: {tries}")
                    tries += 1
                    time.sleep(retries_sleep_second)
            else:
                raise TimeoutError("Reached aiohttp max tries")

        if asyncio.iscoroutinefunction(function):
            return async_wrapped
        else:
            return wrapped

    return wrapper



async def getproxy():
    if Tuski_WX_shopsign_Proxy == None:
        return None
    async with aiohttp.ClientSession() as seesion:
        global proxies,get_proxy_time,IP,port
        # 底下 s.get之后的链接为代理链接 自备
        response =await seesion.get(Tuski_WX_shopsign_Proxy)
        res =await response.text()
        try:
            IP= re.findall('(?:(?:2(?:5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(?:\.(?:(?:2(?:5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}', res)[0]
            port = re.findall(":([0-9]+)", res)[0]
            proxies = f"http://{IP}:{port}"
            logger.warning(f'当前设置代理：{proxies}')
            return proxies
        except:
            logger.warning('获取代理失败')
            proxies = None
            return None
            # sys.exit()


def checkproxy():
    code= 1
    if proxies == None:
        return
    else:
        while True:
            retrys = 0
            while code:
                while 3 > retrys:
                    if time.time() - get_proxy_time < 25:
                        try:
                            telnetlib.Telnet(host=IP, port=port, timeout=3)
                            logger.warning("代理IP有效！")
                            time.sleep(3)
                            retrys = 0
                        except:
                            retrys += 1
                            logger.warning(f"代理IP失效！第{retrys}次重试")
                            getproxy()
                    else:
                        getproxy()
                else:
                    raise TimeoutError("重试获取代理3次失败")
            else:
                time.sleep(1)
                break


@session_manager
async def jdtime(session):  # 京东当前时间
    res = await session.get(url='https://sgm-m.jd.com/h5/', headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36'})
    text = await res.text()
    q = int(json.loads(text)["timestamp"])
    w = time.localtime(q / 1000)
    e = time.strftime("%Y-%m-%d %H:%M:%S", w)
    return q, e



async def get_token(ck,host):  # 获取token
    try:
        function = 'isvObfuscator'
        body = {"url": f"https://{host}", "id": ""}
        token = await getoken(ck, functionId=function, body=body)
        # logger.warning(token)
        return token
    except:
        return f'获取token失败'


async def refreshck(Url, proxies, session: aiohttp.ClientSession):  # 获取set_cookie
    res = await session.get(Url, proxy=proxies)
    if res.status == 200:
        pass
    else:
        raise TimeoutError("IP可能黑了，请更换IP后重试")


async def getSimpleActInfoVo(proxies, actId, host, session: aiohttp.ClientSession):  # 获取venderId
    url = f'https://{host}/customer/getSimpleActInfoVo?activityId={actId}'
    res = await session.post(url=url, proxy=proxies)
    if res.status == 200:
        text = await res.text()
        # logger.warning(text)
        res_json = json.loads(text)
        venderId = res_json["data"]["venderId"]
        shopId = res_json["data"]["shopId"]
        return venderId
    else:
        logger.warning('getSimpleActInfoVo失败')


async def getping(proxies, token, venderId, host, session: aiohttp.ClientSession):  # 获取账号ping值
    url = f'https://{host}/customer/getMyPing?userId={venderId}&token={token}&fromType=APP'
    res = await session.post(url, proxy=proxies)
    if res.status in [200, 201]:
        text = await res.text()
        if "secretPin" in text:
            res_json = json.loads(text)
            secretPin = res_json["data"]["secretPin"]
            if host in ["cjhy-isv.isvjcloud.com", "cjhydz-isv.isvjcloud.com"]:
                if '+' in secretPin:
                    secretPin = quote_plus(secretPin)
            secretPin = quote_plus(secretPin)
            return secretPin
        else:
            logger.warning("获取ping失败")
            return False
    else:
        return False



async def activity(proxies, actId, venderId, secretPin, host, session: aiohttp.ClientSession):  # 获取活动的信息
    url = f'https://{host}/sign/wx/getActivity?actId={actId}&venderId={venderId}'
    cookies = {'AUTH_C_USER': secretPin}
    res = await session.post(url,cookies=cookies, proxy=proxies)
    if res.status == 200:
        text = await res.text()
        # logger.warning(res.status_code)
        if 'act' in text:
            # logger.warning(res.text)
            res_json = json.loads(text)
            return res_json
        else:
            return text
    else:
        return False

async def accessLog(proxies, actId, venderId, secretPin, host, session: aiohttp.ClientSession):  # 获取活动的信息
    url = f'https://{host}/common/accessLog?venderId{venderId}&code=15&pin={secretPin}&activityId={actId}&pageUrl={activityUrl}&subType=&uuid='
    res = await session.post(url, proxy=proxies)
    if res.status == 200:
        return True
    else:
        return False


async def getSignInfo(Url, proxies, actId, secretPin, venderId, host, session: aiohttp.ClientSession):  # 获取活动的信息
    if 'sevenDay' in Url:
        url= f'https://{host}/sign/sevenDay/wx/getSignInfo?actId={actId}&venderId={venderId}&pin={secretPin}'
    else:
        url = f'https://{host}/sign/wx/getSignInfo?venderId={venderId}&pin={secretPin}&actId={actId}'
    res = await session.post(url, proxy=proxies)
    if res.status == 200:
        try:
            json_data = await res.json()
            return json_data
        except Exception as e:
            logger.warning(e)
    else:
        logging.warning("获取签到记录失败")
        return False


async def signUp(Url, proxies, actId, secretPin, venderId, host, session: aiohttp.ClientSession):  # 获取活动的信息
    if 'sevenDay' in Url:
        url= f'https://{host}/sign/sevenDay/wx/signUp?actId={actId}&pin={secretPin}'
    else:
        url = f'https://{host}/sign/wx/signUp?actId={actId}&pin={secretPin}'
    res = await session.post(url, proxy=proxies)
    if res.status == 200:
        try:
            json_data = await res.json()
            return json_data
        except Exception as e:
            text = await res.text()
            return text
    else:
        return False


@with_retries(max_tries=2, retries_sleep_second=1)
async def get_Activity(proxies, Url, cookie, actId, jd_pin, host ,session: aiohttp.ClientSession):
    try:
        session.headers.add('referer', Url)
        session.headers.add('Origin', f'https://{host}')
        session.headers.add('User-Agent', ua)
        session.headers.add('host', host)
        Msg=''
        await refreshck(Url, proxies, session)
        venderId = await getSimpleActInfoVo(proxies, actId, host, session)
        token = await get_token(cookie, host)
        if token == '获取token失败':
            raise ConnectionError(f'{jd_pin}获取token失败')
        secretPin = await getping(proxies, token, venderId, host, session)
        if secretPin == False: raise ConnectionError(f'{jd_pin} 获取ping失败')
        if 'sevenDay' in Url:
            activity_data= await getSignInfo(Url, proxies, actId, secretPin, venderId, host, session)
            if activity_data != False:
                if "该活动已经结束" in activity_data:
                    return False
                gifday = ["1","2","3","4","5","6","7"]
                giflist = ''
                actRule= activity_data["actRule"]
                date = re.findall('[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}', actRule)
                startTime_Array = time.strptime(date[0], "%Y-%m-%d %H:%M")
                endTime_Array = time.strptime(date[1], "%Y-%m-%d %H:%M")
                startTime = int(time.mktime(startTime_Array))
                endTime = int(time.mktime(endTime_Array))
                for i in activity_data["giftConditions"]:
                    try:
                        giflist += f"{activity_data['giftConditions'].index(i)}天{i['gift']['giftName']};"
                    except:
                        continue
                msg = f'活动链接：{activityUrl}\n开始时间：{date[0]}\n结束时间：{date[1]}\n活动奖励：{giflist}'
                Msg += f'{msg}\n'
                logger.warning(msg)
                sign_Info = await signUp(Url, proxies, actId, secretPin, venderId, host, session)
                if sign_Info != False:
                    if sign_Info['isOk'] == True:
                        sign_data["data"][-1]['signed_days'] = 1
                        try:
                            msg = f"{jd_pin}今日签到成功,获得{sign_Info['signResult']['gift']['giftName']}🤩"
                            Msg += f'{msg}\n'
                            logger.warning(msg)
                            send(title='WX_shopsign', content=Msg)
                            return
                        except:
                            msg = f'{jd_pin}签到成功,获得空气 👻'
                            Msg += f'{msg}\n'
                            logger.warning(msg)
                            send(title='WX_shopsign', content=Msg)
                            return
                    else:
                        msg = f"{jd_pin}签到失败：{sign_Info['msg']}"
                        Msg += f'{msg}\n'
                        logger.warning(msg)
                        send(title='WX_shopsign', content=Msg)
                    if int(startTime) + 244800 < int(time.time()):
                        msg = f'开启大于三天，未收录'
                        Msg += msg
                        logger.warning(msg)
                        send(title='WX_shopsign', content=Msg)
                        return '未收录'
                    else:
                        if cookie != cookies[0]:
                            return
                        now = str(datetime.datetime.now().date())
                        now = now.replace('-', '')
                        activity_info = {'activityUrl': activityUrl, 'startTime': startTime, 'endTime': endTime,
                                         'gifday': gifday, 'giflist': giflist, 'signed_days': 1, "lastsigned": str(now)}
                        sign_data["data"].append(activity_info)
                        return
            else:
                logger.warning(f'{Url} 获取活动信息失败')
                return

        else:
            if cookie == cookies[0]:
                activity_data= await activity(proxies, actId, venderId,secretPin, host, session)
                if activity_data != False:
                    if "该活动已经结束" in activity_data:
                        return False
                    gifday=[]
                    giflist=''
                    startTime= int(activity_data['act']['startTime'])/1000
                    startTime_c = localtime(startTime)
                    endTime= int(activity_data['act']['endTime'])/1000
                    endTime_c= localtime(endTime)
                    if activity_data['act']['wxSignActivityGiftBean']['hasGiftEveryDay'] == "y":
                        giflist += f"每天 {activity_data['act']['wxSignActivityGiftBean']['gift']['giftName']};"
                    for i in activity_data['act']['wxSignActivityGiftBean']['giftConditions']:
                        gifday.append(i['dayNum'])
                        giflist += f"{i['dayNum']}天{i['gift']['giftName']};"
                    msg= f'活动链接：{activityUrl}\n开始时间：{time.strftime("%Y-%m-%d %H:%M:%S", startTime_c)}\n结束时间：{time.strftime("%Y-%m-%d %H:%M:%S", endTime_c)}\n活动奖励：{giflist}'
                    Msg += f'{msg}\n'
                    logger.warning(msg)
                    if int(startTime) + 244800 < int(time.time()):
                        msg= f'开启大于三天，未收录'
                        Msg += msg
                        logger.warning(msg)
                        send(title='WX_shopsign', content=Msg)
                        return '未收录'
                    else:
                        activity_info= {'activityUrl': activityUrl, 'startTime': startTime, 'endTime': endTime, 'gifday': gifday, 'giflist':giflist}
                        sign_data["data"].append(activity_info)
                else:
                    logging.info("获取活动信息失败")
                    return False

            # await accessLog(actId, venderId, secretPin, session)
            sign_Info = await getSignInfo(Url, proxies, actId, secretPin, venderId, host, session)
            if sign_Info!= False:
                now = str(datetime.datetime.now().date())
                now = now.replace('-', '')
                signed_days= sign_Info['signRecord']['contiSignNum']
                lastSignDate= str(sign_Info['signRecord']['lastSignDate'])
                if str(lastSignDate) == now:
                    msg= f'今日已签到\n{jd_pin}已签{signed_days}天'
                    if cookie == cookies[0]:
                        sign_data["data"][-1]['lastsigned'] = lastSignDate
                        sign_data["data"][-1]['signed_days'] = signed_days
                    Msg += f'{msg}\n'
                    logger.warning(msg)
                    send(title='WX_shopsign', content=Msg)
                    return
                else:
                    msg= f'今日未签到\n{jd_pin}已签{signed_days}天'
                    Msg += f'{msg}\n'
                    logger.warning(msg)
                    signup_data = await signUp(Url, proxies, actId, secretPin, venderId, host, session)
                    # logger.warning(signup_data)
                    if signup_data['isOk'] == True:
                        if cookie == cookies[0]:
                            sign_data["data"][-1]['lastsigned'] = now
                            sign_data["data"][-1]['signed_days'] = signed_days + 1
                        if signup_data['gift'] in [None,'']:
                            msg= f'签到成功,获得空气 👻'
                            Msg += f'{msg}\n'
                            logger.warning(msg)
                            send(title='WX_shopsign', content=Msg)
                            return
                        else:
                            msg= f"今日签到成功,获得{signup_data['gift']['giftName']}🤩"
                            Msg += f'{msg}\n'
                            logger.warning(msg)
                            send(title='WX_shopsign', content=Msg)
                            return
                    else:
                        msg= f"签到失败：{signup_data['msg']}"
                        Msg += f'{msg}\n'
                        logger.warning(msg)
                        send(title='WX_shopsign', content=Msg)
                        return
    except Exception as e:
        logger.warning(f'{jd_pin}签到失败:{e}')


@with_retries(max_tries=2, retries_sleep_second=1)
async def async_sign(proxies, Url, cookie, actId, jd_pin, host, piece, session: aiohttp.ClientSession):
    try:
        session.headers.add('referer', Url)
        session.headers.add('Origin', f'https://{host}')
        session.headers.add('User-Agent', ua)
        session.headers.add('host', host)
        Msg = ''
        await refreshck(Url, proxies, session)
        venderId = await getSimpleActInfoVo(proxies, actId, host, session)
        token = await get_token(cookie, host)
        if token == '获取token失败':
            raise ConnectionError(f'{jd_pin}获取token失败')
        secretPin = await getping(proxies, token, venderId, host, session)
        if secretPin == False: raise ConnectionError(f'{jd_pin} 获取ping失败')
        now = str(datetime.datetime.now().date())
        now = now.replace('-', '')
        pass
        if 'sevenDay' in Url:
            sign_Info = await signUp(Url, proxies, actId, secretPin, venderId, host, session)
            if sign_Info != False:
                if sign_Info['isOk'] == True:
                    if cookie == cookies[0]:
                        sign_data["data"][piece]['signed_days'] += 1
                        sign_data["data"][piece]['lastsigned'] = now
                    try:
                        msg = f"{jd_pin}今日签到成功,获得{sign_Info['signResult']['gift']['giftName']}🤩"
                        Msg += f'{msg}\n'
                        logger.warning(msg)
                        send(title='WX_shopsign', content=Msg)
                        return
                    except:
                        msg = f'{jd_pin}签到成功,获得空气 👻'
                        Msg += f'{msg}\n'
                        logger.warning(msg)
                        send(title='WX_shopsign', content=Msg)
                        return

                else:
                    msg = f"{jd_pin}签到失败：{sign_Info['msg']}"
                    Msg += f'{msg}\n'
                    logger.warning(msg)
                    send(title='WX_shopsign', content=Msg)
        sign_Info = await getSignInfo(Url, proxies, actId, secretPin, venderId, host, session)
        if sign_Info!= False:
            signed_days= sign_Info['signRecord']['contiSignNum']
            lastSignDate= sign_Info['signRecord']['lastSignDate']
            if str(lastSignDate) == now:
                msg= f'今日已签到\n{jd_pin}已签{signed_days}天'
                if cookie == cookies[0]:
                    sign_data["data"][piece]['signed_days'] = signed_days
                    sign_data["data"][piece]['lastsigned']= now
                Msg += f'{msg}\n'
                logger.warning(msg)
                if Url in award_sign:
                    award_sign.remove(Url)
                return
            else:
                msg= f'今日未签到\n{jd_pin}已签{signed_days}天'
                Msg += f'{msg}\n'
                logger.warning(msg)
                signup_data = await signUp(Url, proxies, actId, secretPin, venderId, host, session)
                # logger.warning(signup_data)
                if signup_data['isOk'] == True:
                    now = str(datetime.datetime.now().date())
                    now = now.replace('-', '')
                    if cookie == cookies[0]:
                        sign_data["data"][piece]['signed_days'] = signed_days + 1
                        sign_data["data"][piece]['lastsigned'] = now
                    if signup_data['gift'] in [None,'']:
                        msg= f'签到成功,获得空气 👻'
                        Msg += f'{msg}\n'
                        logger.warning(msg)
                        if Url in award_sign:
                            award_sign.remove(Url)
                        return
                    else:
                        msg= f"今日签到成功,获得{signup_data['gift']['giftName']}🤩"
                        Msg += f'{msg}\n'
                        logger.warning(msg)
                        if Url in award_sign:
                            award_sign.remove(Url)
                        return
                else:
                    msg= f"签到失败：{signup_data['msg']}"
                    Msg += f'{msg}\n'
                    logger.warning(msg)
                    if Url in award_sign:
                        award_sign.remove(Url)
                    return
    except Exception as e:
        if Url in award_sign:
            award_sign.remove(Url)
        logger.warning(e)


async def proxy_sign(Url, cookie, actId, jd_pin, host, piece):
    proxies= await getproxy()
    await async_sign(proxies, Url, cookie, actId, jd_pin, host, piece)

async def taskmanager(task_sem, cookie, Url, mode, piece):
    # logger.warning(Url)
    rate = cookies.index(cookie)
    jd_pin = re.findall('pt_pin=(.*?);', cookie)[0]
    actId = re.findall('[0-9a-z]{32}', Url)[0]
    host = re.findall('https?://((?:[\w-]+\.)+\w+(?::\d{1,5})?)', Url)[0]
    if mode == 1:
        now= datetime.datetime.now()
        scheduler.add_job(proxy_sign, 'date', run_date=datetime.datetime(now.year, now.month, now.day+1, 0, 0, rate * 1),args=[Url, cookie, actId, jd_pin, host, piece])
        # now = int(time.time())
        # await asyncio.sleep(zerotime - now + len(cookies) * 3)
    else:
        async with task_sem:
            proxies=await getproxy()
            await async_sign(proxies, Url, cookie, actId, jd_pin, host, piece)


async def cookiemanager(Task_sem, Url, mode, piece):
    task = []
    task_sem = asyncio.Semaphore(20)
    async with Task_sem:
        for cookie in cookies:
            task.append(asyncio.create_task(taskmanager(task_sem, cookie, Url, mode, piece)))
            await asyncio.sleep(1)
        await asyncio.gather(*task)




async def main():
    if activityUrl == None:
        pass
    else:
        if activityUrl in str(sign_data):
            pass
        else:
            cookie= cookies[0]
            jd_pin = re.findall('pt_pin=(.*?);', cookie)[0]
            actId = re.findall('[0-9a-z]{32}', activityUrl)[0]
            host = re.findall('https?://((?:[\w-]+\.)+\w+(?::\d{1,5})?)', activityUrl)[0]
            proxies= await getproxy()
            Url = activityUrl
            Activity = await get_Activity(proxies, Url, cookie, actId, jd_pin, host)
            if Activity == '未收录':
                pass
            else:
                for cookie in cookies[1:-1]:
                    jd_pin = re.findall('pt_pin=(.*?);', cookie)[0]
                    await get_Activity(proxies, Url, cookie, actId, jd_pin, host)
    Task=[]
    now = datetime.datetime.now()
    Sign_data = copy.deepcopy(sign_data)
    logger.warning(f'#'* 50)
    if now.hour == 23 and now.minute >= 50:
        Task_sem = asyncio.Semaphore(len(sign_data["data"]))
        logger.warning('距离零点小于20分钟，执行定时模式')
        for Activity_info in sign_data["data"]:
            if str(Activity_info["signed_days"] + 1) in Activity_info["gifday"]:
                piece = sign_data["data"].index(Activity_info)
                Sign_data["data"].remove(Activity_info)
                mode = 1
                Url = Activity_info['activityUrl']
                award_sign.append(Url)
                Task.append(asyncio.create_task(cookiemanager(Task_sem, Url, mode, piece)))
        await asyncio.gather(*Task)
        scheduler.start()
        while True:
            if len(award_sign) == 0:
                break
            await asyncio.sleep(1)
        Task.clear()
        mode = 2
        for Activity_info in Sign_data["data"]:
            Url = Activity_info['activityUrl']
            piece = sign_data["data"].index(Activity_info)
            Task.append(asyncio.create_task(cookiemanager(Task_sem, Url, mode, piece)))
        await asyncio.gather(*Task)

    else:
        now = str(datetime.datetime.now().date())
        now = now.replace('-', '')
        for Activity_info in sign_data["data"]:
            if int(Activity_info['lastsigned']) == int(now):
                Sign_data["data"].remove(Activity_info)
                Url = Activity_info['activityUrl']
                logger.warning(f'{Url} 今日已签，跳过')
        Task_sem = asyncio.Semaphore(len(Sign_data["data"]))
        mode = 2
        logger.warning(f'#' * 50)
        for Activity_info in Sign_data["data"]:
            piece = sign_data["data"].index(Activity_info)
            Url = Activity_info['activityUrl']
            Task.append(asyncio.create_task(cookiemanager(Task_sem, Url, mode, piece)))
        await asyncio.gather(*Task)

    await cache_write()



if __name__ == '__main__':
    try:
        cookies = getck()
    except Exception as e:
        logger.warning("获取ck失败")
        sys.exit()
    try:
        activityUrl = os.environ.get("Tuski_WX_shopsign")
        logger.warning(f'活动链接：{activityUrl}')
    except Exception as e:
        logger.warning("获取活动链接失败")
        logger.warning('即将执行缓存签到')
    try:
        Tuski_WX_shopsign_Proxy = os.environ.get("Tuski_WX_shopsign_Proxy")
        logger.warning(f'代理链接：{Tuski_WX_shopsign_Proxy}')
    except Exception as e:
        logger.warning("未设置代理")
        Tuski_WX_shopsign_Proxy= None
    sign_data = read_cache()
    zerotime = int(time.mktime(datetime.date.today().timetuple())) + 86400
    task = []
    ua = UserAgent().random
    logger.warning("="*50)
    # thread = threading.Thread(target=getproxy, name="获取代理")
    loop= asyncio.get_event_loop()
    loop.run_until_complete(main())
