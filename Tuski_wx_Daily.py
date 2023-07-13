#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lz，cj无线组队脚本  BY.Tuski
版本： 2.0
环境变量 活动url： export Tuski_WX_Daily="活动url"
        线程数： 默认10线程
        代理：无代理
TG: https://t.me/cooooooCC
new Env('Tuski_每日抢（interactsaas）');
禁用就行 Tuski_wx_Daily.py
"""

import asyncio
import aiohttp
import json, re, os, sys, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from asgetoken import getoken
from urllib.parse import quote_plus, unquote_plus
from session import with_retries
from Get_cookies import getck
from sendNotify import send
from fake_useragent import UserAgent
import logging
from datetime import datetime

Ing=[]
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


class daily:
    def __init__(self, cookie, AcitivityUrl):
        self.ActivityUrl= AcitivityUrl
        self.jd_pin = unquote_plus(re.findall('pt_pin=(.*?);', cookie)[0])
        self.AcitivityId = re.findall('[\w]{19}', self.ActivityUrl)[0]
        self.host = re.findall('https?://((?:[\w-]+\.)+\w+(?::\d{1,5})?)', self.ActivityUrl)[0]
        self.cookie = cookie
        self.function = 'isvObfuscator'
        self.body = {"url": f"https://{self.host}", "id": ""}
        self.ua= UserAgent().random


    async def get_Token(self, session: aiohttp.ClientSession):
        url=f'https://lzkj-isv.isvjcloud.com/prod/cc/interactsaas/api/user-info/login?'
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Referer': self.ActivityUrl,
            'User-Agent': self.ua,
        }
        token = await getoken(self.cookie, functionId=self.function, body=self.body)
        data={
            'activityId' : '1674704784617754625',
            'shareUserId' : '',
            'source' : '01',
            'status' : '1',
            'tokenPin' : token,
            'uuid' : ''
        }
        res=await session.post(url,headers=headers, data= json.dumps(data))
        if res.status == 200 :
            try:
                global shopName
                res_json= await res.json()
                shopName= res_json["data"]["shopName"]
                Token= res_json["data"]["token"]
                return Token
            except  Exception as e:
                logger.warning(f'Token请求失败:{e}')
        else:
            logger.warning(f'Token请求失败: 403')
            raise asyncio.TimeoutError


    async def get_Activity(self, Token, session: aiohttp.ClientSession):
        url = 'https://lzkj-isv.isvjcloud.com/prod/cc/interactsaas/api/task/dailyGrabs/activity'
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Referer': self.ActivityUrl,
            'User-Agent': self.ua,
            'Token': Token
        }
        res=await session.post(url, headers=headers)
        if res.status == 200:
            try:
                res_json= await res.json()
                return res_json
            except Exception as e:
                logger.warning(f'请求Activity失败: {e}')
        else:
            logger.warning(f'请求Activity失败: 403')
            raise TimeoutError


    @with_retries(max_tries=3, retries_sleep_second=0.2)
    async def dayReceive(self, Token, prizeInfoId,  session: aiohttp.ClientSession):
        # jd_pin = unquote_plus(re.findall('pt_pin=(.*?);', self.cookie)[0])
        # ua = UserAgent().random
        url = 'https://lzkj-isv.isvjcloud.com/prod/cc/interactsaas/api/task/dailyGrabs/dayReceive'
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Referer': ActivityUrl,
            'User-Agent': self.ua,
            'Token': Token
        }
        data={
            'prizeInfoId' : prizeInfoId
        }
        res = await session.post(url, headers=headers, data= json.dumps(data))
        if res.status == 200:
            try:
                res_json = await res.json()
                # print(res_json)
                if "data" in str(res_json):
                    meg= f'{self.jd_pin}获得{res_json["data"]["prizeName"]}'
                    logger.warning(meg)
                    send('Tuski_100抢豆豆', meg)
                    if self.cookie in Ing:
                        Ing.remove(self.cookie)
                else:
                    logger.warning(f'{res_json["resp_msg"]}')
            except Exception as e:
                logger.warning(f'请求Activity失败: {e}')
        else:
            logger.warning(f'请求抢豆失败: 403')
            raise asyncio.TimeoutError
        if self.cookie in Ing:
            Ing.remove(self.cookie)


@with_retries(max_tries=2, retries_sleep_second=1)
async def Taskmanager(cookie, session: aiohttp.ClientSession):
    Daily= daily(cookie, ActivityUrl)
    Token= await Daily.get_Token(session)
    if Token != None:
        Activity_data = await Daily.get_Activity(Token,session)
        if Activity_data != None:
            startTime= Activity_data["data"]["activityStartTime"]/1000
            endTime = Activity_data["data"]["activityEndTime"] / 1000
            lotteryTime= Activity_data["data"]["lotteryTime"] / 1000
            prizeInfoId= Activity_data["data"]["prizeInfoId"]
            prizeName= Activity_data["data"]["prizeName"]
            surplusDayNum= Activity_data["data"]["surplusDayNum"]
            startTime_c = time.localtime(startTime)
            endTime_c = time.localtime(endTime)
            lotteryTime_c= time.localtime(lotteryTime)
            mes= f'每日抢：{ActivityUrl}\n店铺：{shopName}\n奖品：{prizeName}\n开始时间：{time.strftime("%Y-%m-%d %H:%M:%S", startTime_c)}\n结束时间：{time.strftime("%Y-%m-%d %H:%M:%S", endTime_c)}\n本轮开抢时间：{time.strftime("%Y-%m-%d %H:%M:%S", lotteryTime_c)}\n数量：{surplusDayNum}份'
            logger.warning(mes)
            now= int(time.time())
            if now > endTime:
                Msg= f'活动已结束'
                mes += f'\n\n{Msg}'
                logger.warning(Msg)
                return mes
            if startTime > now:
                Msg = f'活动已未开始'
                mes += f'\n\n{Msg}'
                logger.warning(Msg)
                return mes
            if now + 480 > lotteryTime  > now:
                Msg = f'活动将于{lotteryTime-now}秒开始, 定时ing'
                mes += f'\n\n{Msg}'
                logger.warning(Msg)
                send('Tuski_100抢豆豆', mes)
                start_time = datetime.fromtimestamp(lotteryTime)
                scheduler.add_job(daily(cookie, ActivityUrl).dayReceive, 'date', run_date=start_time, args=[Token, prizeInfoId])
                Ing.append(cookie)
            else:
                logger.warning(f'开抢时间大于8分钟， pass')
    return


async def main():
    if ActivityUrl == None:
        return
    Task= []
    await Taskmanager(cookies[0])
    if len(Ing) != 0:
        for cookie in cookies[1:9]:
            Task.append(asyncio.create_task(Taskmanager(cookie)))
        await asyncio.gather(*Task)
        scheduler.start()
        while True:
            if len(Ing) == 0:
                break
            await asyncio.sleep(1)
    else:
        pass

if __name__ == '__main__':
    try:
        cookies = getck()
    except Exception as e:
        logger.warning("获取ck失败")
        sys.exit()
    try:
        ActivityUrl = os.environ.get("Tuski_wx_Daily")
        logger.warning(f'活动链接：{ActivityUrl}')
    except Exception as e:
        logger.warning("获取活动链接失败")
        sys.exit()
    asyncio.run(main())
