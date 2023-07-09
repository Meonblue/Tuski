"""
20 店铺签到  BY.Tuski
版本： 2.0
Tuski_shopSign_token 活动token，多个请用 | 相隔
TG: https://t.me/cooooooCC
脚本会在距离第二天零点前五分钟自动定时，建议签到定时提前5分钟
每天执行三四遍即可  防止断签
new Env('Tuski_店铺签到');
建议定时：
2 57 8,23 * * * Tuski_shopsign.py
"""


from fake_useragent import UserAgent
from aiohttp import ClientSession
import time
import json
import asyncio
import datetime
import os, sys, re
from h5st31 import h5st31
import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging
from Get_cookies import getck
from sendNotify import send
from session import with_retries


logging.basicConfig(level=logging.WARNING, format='%(message)s')
logging.getLogger('apscheduler').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def jdtime():
    url = 'https://sgm-m.jd.com/h5/'
    headers = {
        'User-Agent': ua
    }
    async with ClientSession() as s:
        async with s.get(url, headers=headers, timeout=1) as res:
            text = await res.text()
            q = int(json.loads(text)["timestamp"])
            w = time.localtime(q / 1000)
            e = time.strftime("%Y-%m-%d %H:%M:%S", w)
            return q, e


async def get_h5st(pin, functionId, body):
    new_h5st31 = h5st31({
        'appId': '4da33',  # h5st里面的appId
        "appid": "interCenter_shopSign",
        "clientVersion": "1.2.5",
        "client": "android",
        "pin": pin,
        "ua": ua
    })
    new_h5st31.genAlgo()
    h5st= new_h5st31.getbody(functionId, body, code=True)
    return h5st


@with_retries(max_tries=5, retries_sleep_second=0)
async def getvenderId(token, session):
    functionId = 'interact_center_shopSign_getActivityInfo'
    body = {"token": token, "venderId": ""}
    pin = re.findall('pt_pin=(.*?);', CookieJDs[0])[0]
    headers = {
        "cookie": CookieJDs[0],
        "referer": 'https://h5.m.jd.com/'
    }
    # appid= "interCenter_shopSign"
    h5st= await get_h5st(pin, functionId, body)
    url = f'https://api.m.jd.com/api?{h5st}'
    response=await session.get(url=url, headers=headers)
    if response.status == 200:
        text = await response.text()
        r = json.loads(text)
        if '当前不存在' in r:
            logger.warning('当前不存在有效的活动，删除!')
        else:
            l = []
            days = []
            try:
                for i in r["data"]["continuePrizeRuleList"]:
                    for x in i["prizeList"]:
                        day = i["days"]
                        days.append(day)
                        prize = int(x["discount"])
                        if x["status"] == 2:
                            status = "有"
                        else:
                            status = "无"
                        if x["type"] == 4:
                            l.append(f'签到{day}天，可得{prize}豆 {status}')
                        elif x["type"] == 10:
                            l.append(f'签到{day}天，可得{prize}E卡 {status}')
                        elif x["type"] == 14:
                            l.append(f'签到{day}天，可得{prize / 100}红包 {status}')
                        elif x["type"] == 6:
                            # logger.warning('店铺积分 忽略')
                            continue
                        elif x["type"] == 9:
                            # logger.warning('商品专享价 忽略')
                            continue
            except Exception as e:
                logger.warning(f'{token}读取活动数据失败，跳过')
            else:
                stimestamp = int(r["data"]["startTime"] / 1000)
                starttime = time.localtime(stimestamp)
                j = time.strftime("%Y-%m-%d %H:%M:%S", starttime)
                endtime = time.localtime(r["data"]["endTime"] / 1000)
                h = time.strftime("%Y-%m-%d %H:%M:%S", endtime)
                activityId = r["data"]["id"]
                venderId = r["data"]["venderId"]
                logger.warning(f'{token}\n开始时间：{j}\n结束时间：{h}\n{l}')
                return [token, venderId, activityId, stimestamp, days]

    else:
        logger.warning('该Token请求接口返回异常，删除!')


@with_retries(max_tries=5, retries_sleep_second=0)
async def getSignRecord(token, venderId, activityId, stimestamp, days, session):
    t = await jdtime()
    url = f'https://api.m.jd.com/api?appid=interCenter_shopSign&t={t[0]}&loginType=2&functionId=interact_center_shopSign_getSignRecord&body={{"token":"{token}","venderId":{venderId},"activityId":{activityId},"type":56,"actionType":7}}'
    headers = {
        "cookie": CookieJDs[0],
        "referer": f'https://h5.m.jd.com/babelDiy/Zeus/2PAAf74aG3D61qvfKUM5dxUssJQ9/index.html?token={token}&sceneval=2&jxsid=16105853541009626903&cu=true&utm_source=kong&utm_medium=jingfen&utm_campaign=t_1001280291_&utm_term=fa3f8f38c56f44e2b4bfc2f37bce9713',
    }
    response=await session.get(url=url, headers=headers)
    d = await response.json()
    day = d["data"]["days"]
    logger.warning(f'当前token：{token}  已签{day}天')
    besignday = (zerotime - stimestamp) / 86400
    if day + 1 in days:
        logger.warning(f'奖励签：{token}')
        awardsign["data"].append(
            {"token": token, "venderId": venderId, "activityId": activityId, "stimestamp": stimestamp})
    elif day >= max(days):
        logger.warning(f"当前token：{token} 已满签，跳过")
        efficienttoken["data"].remove(
            {"token": token, "venderId": venderId, "activityId": activityId, "stimestamp": stimestamp,
             "awardays": days})
    elif day+2 < besignday:
        logger.warning(f'当前token：{token} 中途有断签到，跳过')
        efficienttoken["data"].remove(
            {"token": token, "venderId": venderId, "activityId": activityId, "stimestamp": stimestamp,
             "awardays": days})


@with_retries(max_tries=5, retries_sleep_second=0)
async def signCollectGift(cookie, token, venderId, activityId, session):
    pin = re.findall('pt_pin=(.*?);', cookie)[0]
    functionId = 'interact_center_shopSign_signCollectGift'
    body = {"token": token, "venderId": f"{venderId}", "activityId": f"{activityId}", "type": 56, "actionType": 7}
    h5st = await get_h5st(pin, functionId, body)
    url = f'https://api.m.jd.com/api?{h5st}'
    headers = {
        "cookie": cookie,
        "referer": 'https://h5.m.jd.com/'
    }
    retry = 0
    while retry < retrys:
        response= await session.get(url=url, headers=headers, timeout=0.5)
        try:
            json_data= await response.json()
        except Exception as e:
            logger.warning(f'第{retry}次签到失败')
            retry = retry + 1
            continue
        if json_data["code"] in ["-1", 402, 3030001, 403000002]:
            logger.warning(f'第{retry}次签到失败')
            retry = retry + 1
            continue
        else:
            if json_data["code"] == 200:
                logger.warning(f'token：{token} 今日签到成功')
                if len(json_data["data"]) == 0:
                    pass
                else:
                    awards = json_data["data"]
                    for i in awards:
                        for X in i["prizeList"]:
                            if X["type"] == 6:
                                logger.warning(f'获得奖励： 获得{int(X["discount"])} 积分')
                            elif X["type"] == 4:
                                logger.warning(f'获得奖励： 获得{int(X["discount"])} 豆')
                            elif X["type"] == 14:
                                logger.warning(f'获得奖励： 获得{int(X["discount"])} 红包')
                            elif X["type"] == 10:
                                logger.warning(f'获得奖励： 获得{int(X["discount"])} E卡')
                            else:
                                logger.warning("不知道获取了啥子奖励")
            elif json_data["code"] == 403030023:
                logger.warning(f'token：{token} 今天已签过到')
            elif "未登录" in json_data:
                logger.warning(f"该ck：{pin} 疑似失效, 跳过")
            elif "用户达到签到上限" in json_data:
                logger.warning(f"该ck：{pin} 今日已达20个签到上限")
            else:
                logger.warning(json_data)
            return
    else:
        logger.warning(f'签到重试超过{retrys}次，退出签到')

@with_retries(max_tries=5, retries_sleep_second=0)
async def async_signCollectGift(cookie, token, h5st, pin, session):
    pin = re.findall('pt_pin=(.*?);', cookie)[0]
    url = f'https://api.m.jd.com/api?{h5st}'
    headers = {
        "cookie": cookie,
        "referer": 'https://h5.m.jd.com/'
    }
    retry = 0
    while retry < retrys:
        response= await session.get(url=url, headers=headers, timeout=0.5)
        try:
            json_data= await response.json()
        except Exception as e:
            logger.warning(f'第{retry}次签到失败')
            retry = retry + 1
            continue
        if json_data["code"] in ["-1", 402, 3030001, 403000002]:
            logger.warning(f'第{retry}次签到失败')
            retry = retry + 1
            continue
        else:
            if json_data["code"] == 200:
                logger.warning(f'{token} 今日签到成功')
                if len(json_data["data"]) == 0:
                    pass
                else:
                    awards = json_data["data"]
                    for i in awards:
                        for X in i["prizeList"]:
                            if X["type"] == 6:
                                msg= f'{pin}获得奖励： 获得{int(X["discount"])} 积分'
                            elif X["type"] == 4:
                                msg = f'{pin}获得奖励： 获得{int(X["discount"])} 豆'
                            elif X["type"] == 14:
                                msg = f'{pin}获得奖励： 获得{int(X["discount"])} 红包'
                            elif X["type"] == 10:
                                msg = f'{pin}获得奖励： 获得{int(X["discount"])} E卡'
                            else:
                                msg = "不知道获取了啥子奖励"
                            Msg += msg
                            logger.warning(msg)
            elif json_data["code"] == 403030023:
                logger.warning(f'token：{token} 今天已签过到')
            elif "未登录" in json_data:
                logger.warning(f"该ck：{pin} 疑似失效, 跳过")
            elif "用户达到签到上限" in json_data:
                logger.warning(f"该ck：{pin} 今日已达20个签到上限")
            else:
                logger.warning(json_data)
            return
    else:
        logger.warning(f'签到重试超过{retrys}次，退出签到')


async def main():
    global Msg
    Msg = ''
    tasks = []
    for i in tokens:
        done = await getvenderId(i)
        if done != None:
            efficienttoken["data"].append(
                {"token": done[0], "venderId": done[1], "activityId": done[2], "stimestamp": done[3], "awardays": done[4]})
            await asyncio.sleep(0.5)
        else:
            pass
    for k in efficienttoken["data"]:
        token = k["token"]
        venderId = k["venderId"]
        activityId = k["activityId"]
        stimestamp = k["stimestamp"]
        days = k["awardays"]
        tasks.append(asyncio.create_task(getSignRecord(token, venderId, activityId, stimestamp, days)))
    done, _ = await asyncio.wait(tasks)
    if len(awardsign["data"]) == 0:
        logger.warning("当前无有奖励签到，跳出并发签到")
    else:
        now = datetime.datetime.now()
        if now.hour == 23 and now.minute >= 57:
            logger.warning(f"即将并发签到{len(awardsign['data'])}个token")
            for v in awardsign["data"]:
                logger.warning(v["token"])
            now = datetime.datetime.now()
            logger.warning(f'当前时间：{now},{60-now.minute}分{60-now.second}秒之后执行签到\n'+ '='*60)
            rate=0
            for cookie in CookieJDs:
                pin = re.findall('pt_pin=(.*?);', cookie)[0]
                for be_signd_token in awardsign["data"]:
                    token = be_signd_token["token"]
                    venderId = be_signd_token["venderId"]
                    activityId = be_signd_token["activityId"]
                    functionId = 'interact_center_shopSign_signCollectGift'
                    body = {"token": token, "venderId": f"{venderId}", "activityId": f"{activityId}", "type": 56,"actionType": 7}
                    h5st= await get_h5st(pin, functionId, body)
                    scheduler.add_job(async_signCollectGift, 'date', run_date=datetime.datetime(now.year, now.month, now.day+1, 0, 0, rate * 2),args=[cookie, token, h5st, pin])
                    time.sleep(2)
                rate = rate + 1
            scheduler.start()
            while True:
                logger.warning(f"-----即将并发签到 1-{len(CookieJDs)} 账号----------")
                now= int(time.time())
                await asyncio.sleep(zerotime- now + 20)
                logger.warning("="* 59)
                break
        else:
            logger.warning('当前时间距离零点大于半小时，执行常规签到')
            pass
    if len(efficienttoken["data"]) == 0:
        logger.warning("当前无token，退出脚本ing")
        sys.exit()
    else:
        logger.warning(f"即将常规签到{len(efficienttoken['data'])}个token")
        for v in efficienttoken["data"]:
            logger.warning(v["token"])
        Rate = 1
        for cookie in CookieJDs:
            ck = re.findall('pt_pin=(.*?);', cookie)[0]
            logger.warning(f"-----正在运行账号{Rate}：{ck}----------")
            for be_signd_token in efficienttoken["data"]:
                token = be_signd_token["token"]
                venderId = be_signd_token["venderId"]
                activityId = be_signd_token["activityId"]
                await signCollectGift(cookie, token, venderId, activityId)
                await asyncio.sleep(1)
            Rate += 1
    send('Tuski_店签',Msg)
    return


if __name__ == '__main__':

    scheduler = AsyncIOScheduler(timezone='Asia/Shanghai')
    timeout = aiohttp.ClientTimeout()
    ua = UserAgent().random
    CookieJDs = getck()
    zerotime= int(time.mktime(datetime.date.today().timetuple())) + 86400
    try:
        tokens = os.environ.get("Tuski_shopSign_token").split('|')
    except Exception as e:
        logger.warning(f"获取tokens失败：{e}")
        sys.exit()
    retrys = 5  # 重试次数
    efficienttoken = {"data": []}
    awardsign = {"data": []}
    general = {"data": []}
    loop= asyncio.get_event_loop()
    loop.run_until_complete(main())
