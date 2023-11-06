#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lz，cj无线组队脚本  BY.Tuski
版本： 3.0
环境变量 活动url： export Tuski_WX_TEAM="活动url"
        线程数： Tuski_WX_TEAM_thread 如未设置默认4线程
        车头数： Tuski_WX_TEAM_capainters 如未设置默认3车头
        代理：Tuski_WX_TEAM_Proxy
TG: https://t.me/cooooooCC
new Env('Tuski_组队');
监控本子 禁用就行 Tuski_WX_TEAM.py
"""

import asyncio
from datetime import datetime

import random
import aiohttp
import json, re, os, sys, time
from asgetoken import getoken
from urllib.parse import quote_plus, unquote_plus
import threading
from Get_cookies import getck
from sendNotify import send
from session import with_retries
from fake_useragent import UserAgent
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

Msg = []
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

Proxy= "http://api2.xkdaili.com/tools/XApi.ashx?apikey=XKD27ED9C9A59F5C7518&qty=1&format=txt&split=0&sign=ec0c7e0d5acc6e950b7939ed18eb6ce2"


@with_retries(max_tries=2, retries_sleep_second=0.5)
async def getproxy(session):
    if Proxy == None:
        proxies = None
        return proxies
    response =await session.get(Proxy)
    res =await response.text()

    try:
        IP = \
            re.findall('(?:(?:2(?:5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(?:\.(?:(?:2(?:5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}',
                       res)[0]
        port = re.findall(":([0-9]+)", res)[0]
        proxies = f'http://{IP}:{port}'
        logger.warning(f'当前设置代理：{proxies}')
        return proxies
    except:
        logger.warning('获取代理失败, 未设置代理')
        proxies = None
        return proxies




async def jdtime():  # 当前时间
    q = int(time.time()*1000)
    w = time.localtime(q / 1000)
    e = time.strftime("%Y-%m-%d %H:%M:%S", w)
    return q, e


class wx_Team:
    def __init__(self, cookie, proxies, session: aiohttp.ClientSession):
        self.Msg = []
        self.cookie = cookie
        self.ua = UserAgent().random
        self.jd_pin = unquote_plus(re.findall('pt_pin=(.*?);', cookie)[0])
        self.session = session
        self.proxies = proxies

    async def get_token(self):  # 获取token
        try:
            function = 'isvObfuscator'
            body = {"url": f"https://{host}", "id": ""}
            token = await getoken(self.cookie, functionId=function, body=body, proxies=self. proxies)
            # print(token)
            return token
        except:
            logger.warning('获取token失败')
            return False


    async def refreshcookie(self):
        # print(self.proxies)
        headers = {
            'Host': host,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'User-Agent': self.ua,
            'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        res = await self.session.get(ActivityUrl, headers=headers, proxy= self.proxies)
        if res.status != 200:
            logger.warning(f"{self.jd_pin}refreshck 失败， 重试一次")
            res = await self.session.get(ActivityUrl, headers=headers, proxy=self.proxies)
            if res.status != 200:
                return
        else:
            return True

    async def getSimpleActInfoVo(self):  # 获取venderId
        url = f'https://{host}/customer/getSimpleActInfoVo'
        haeders = {
            'Host': host,
            'Connection': 'keep - alive',
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': self.ua,
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'Origin': f'https://{host}',
            'Referer': ActivityUrl,
        }
        body = f'activityId={activityId}'
        res = await self.session.post(url=url, headers=haeders, params=body, proxy=self.proxies)
        if res.status == 200:
            res_json = await res.json()
            global venderId, shopId
            venderId = res_json["data"]["venderId"]
            shopId = res_json["data"]["shopId"]
        else:
            logger.warning('getSimpleActInfoVo失败')
            return

    async def shopinfo(self):  # 获取店铺名
        url = f'https://{host}/wxTeam/shopInfo?activityId={activityId}'
        haeders = {
            'Host': host,
            'User-Agent': self.ua,
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'Origin': f'https://{host}',
            'Referer': ActivityUrl,
        }
        res = await self.session.post(url, headers=haeders, proxy=self.proxies)
        if res.status == 200:
            res_json = await res.json()
            shopName = res_json["data"]["shopName"]
            return shopName
        else:
            return False

    async def getDefenseUrls(self):
        url = "https://cjhy-isv.isvjcloud.com/customer/getDefenseUrls"
        await self.session.get(url)

    async def get_secretPin(self, token, venderId):  # 获取账号ping值
        def random_str(num):
            random_uuid = ""
            for i in range(num):
                random_uuid = random_uuid + random.choice("abcdefghijklmnopqrstuvwxyz0123456789")
            return random_uuid

        Times = int(time.time() * 1000)
        url = f'https://{host}/customer/initPinToken?activityId={activityId}&jdToken={token}&source=01&venderId={venderId}&uuid={random_str(16)}&clientTime={Times}&fromType=WeChat&riskType=1'
        await self.getDefenseUrls()
        res = await self.session.post(url, proxy=self.proxies)
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

    async def activityContent(self, secretPin):  # 获取活动的信息
        url = f'https://{host}/wxTeam/activityContent'
        data = f"activityId={activityId}&pin={secretPin}&signUuid="
        haeders = {
            'Host': host,
            'User-Agent': self.ua,
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'Origin': f'https://{host}',
            'Referer': ActivityUrl,
        }
        res = await self.session.post(url, headers=haeders, data=data, proxy=self.proxies)
        if res.status == 200:
            try:
                res_json = await res.json()
                return res_json
            except:
                logger.warning(Exception)
                return False
        else:
            logger.warning(f"{self.jd_pin} 获取activityContent 失败")
            return False

    async def saveCaptain(self, secretPin):  # 建队
        url = f'https://{host}/wxTeam/saveCaptain?activityId={activityId}&pin={secretPin}&pinImg=&venderId={venderId}'
        haeders = {
            'Host': host,
            'User-Agent': self.ua,
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'Origin': f'https://{host}',
            'Referer': ActivityUrl,
        }
        t = 0
        while t < 3:
            res = await self.session.post(url, headers=haeders, proxy=self.proxies)
            if res.status == 200:
                return await res.text()
            else:
                t += 1
                logger.warning(f'第{t}次建队失败')
        else:
            logger.warning(f"建队重试大于三次，跳过此cookie")
            return False

    async def saveMember(self, signUuid, secretPin):  # 加入队伍
        url = f'https://{host}/wxTeam/saveMember?activityId={activityId}&signUuid={signUuid}&pin={secretPin}&pinImg=&venderId={venderId}'
        # data =f"activityId={activityId}&signUuid={signUuid}&pin={secretPin}&pinImg=&venderId={venderId}"
        haeders = {
            'Host': host,
            'User-Agent': self.ua,
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'Origin': f'https://{host}',
            'Referer': ActivityUrl,
        }
        t = 0
        while t < 2:
            res = await self.session.post(url, headers=haeders, proxy=self.proxies)
            if res.status == 200:
                text = await res.text()
                return text
            else:
                t += 1
                logger.warning(f'第{t}次入队失败')
        else:
            logger.warning(f"入队重试大于三次，跳过此cookie")
            return

    async def bindWithVender(self):
        try:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'User-Agent': self.ua,
                'Cookie': self.cookie,
                'Host': 'api.m.jd.com',
                'Referer': 'https://shopmember.m.jd.com/',
                'origin': 'https://shopmember.m.jd.com',
                "activityId": activityId
            }
            params = {
                'appid': 'shopmember_m_jd_com',
                'functionId': 'bindWithVender',
                'body': json.dumps({
                    "venderId": venderId,
                    "shopId": shopId,
                    "bindByVerifyCodeFlag": 1,
                    "registerExtend": {},
                    "writeChildFlag": 0,
                    "channel": 406
                }),
                'client': 'H5',
                'clientVersion': '9.2.0',
                'h5st': 'h5st=20230130135600389%3B2940316556511862%3Bef79a%3Btk02w99301bec18nQBAh5uEnWvcASJn6eAMz2II1xsAFUwEQaOb9UTawLkayh1lS%2FWDN7bZlXG2KQoTnNapQ1O1Pddbv%3Baac1d1b08b8628cb389e37e6344afadcc5701605ed6d65ebc12c6c68150a2f9c%3B3.0%3B1675058160389'

            }
            res = await self.session.post('https://api.m.jd.com/', headers=headers, params=params)
            text = await res.text()
            res_json = json.loads(text)
            if res_json['success']:
                logger.warning(f"{self.jd_pin}入会成功")
                logger.warning(res_json)
                return True
        except Exception as e:
            logger.warning(f"{self.jd_pin}入会失败: {e}")
            return False




@with_retries(max_tries=2, retries_sleep_second=0.5)
async def get_Actinfo(cookie, proxies, session):
    jd_pin = unquote_plus(re.findall('pt_pin=(.*?);', cookie)[0])
    Team = wx_Team(cookie, proxies, session)
    token = await Team.get_token()
    # print(f"{jd_pin} token= {token}")
    if token:
        if await Team.refreshcookie():
            await Team.getSimpleActInfoVo()
            secretPin = await Team.get_secretPin(token, venderId)
            if secretPin:
                res_json = await Team.activityContent(secretPin)
                # logger.warning(res_json)
                if res_json:
                    global maxGroup, startTime
                    successRetList = res_json['data']['successRetList']
                    signUuid = res_json["data"]["signUuid"]
                    if cookie == capainters[0]:
                        actName = res_json["data"]["active"]["actName"]
                        maxGroup = res_json["data"]["active"]["maxGroup"]
                        startTime = res_json["data"]["active"]["startTime"]
                        endTime = res_json["data"]["active"]["endTime"]
                        actRule = str(res_json["data"]["active"]["actRule"]).split('\r\n')
                        rulers = f'{actRule[0]}\n{actRule[1]}\n{actRule[2]}\n{actRule[3]}'
                        # team_list= res_json['data']['list']
                        shopName = await Team.shopinfo()
                        cookies.remove(cookies[0])
                        cookies.insert(maxGroup * 4 + 3, capainters[0])
                        if shopName:
                            msg = f'🐹🐹 -- 当前奖励详情 -- 🐽🐽\n店铺：{shopName}\n 活动链接：{ActivityUrl}\n活动名称:{actName}\n活动明细:\n{rulers}'
                            logger.warning(msg)
                            Msg.append(msg)
                        else:
                            msg = f'🐹🐹 -- 当前奖励详情 -- 🐽🐽\n店铺：{shopName}\n 活动链接：{ActivityUrl}\n活动名称:{actName}\n活动明细:\n{rulers}'
                            logger.warning(msg)
                            Msg.append(msg)
                        jdtime_now = await jdtime()
                        q, e = jdtime_now[0], jdtime_now[1]
                        if endTime < q:
                            msg= "\n活动已结束!"
                            logger.warning(msg)
                            Msg.append(msg)
                            return "活动已结束!"
                        if successRetList is None:
                            logger.warning(f"{jd_pin} 未开始组队")
                            need_num = maxGroup * 4
                            return signUuid, secretPin, need_num
                        elif maxGroup == len(successRetList):
                            msg = f"\n{jd_pin}已组满"
                            logger.warning(msg)
                            Msg.append(msg)
                            return "已组满"
                        else:
                            need_num = (maxGroup - len(successRetList)) * 4
                            return signUuid, secretPin, need_num

                    else:
                        if successRetList is None:
                            logger.warning(f"{jd_pin} 未开始组队")
                            need_num = maxGroup * 4
                            return signUuid, secretPin, need_num
                        elif maxGroup == len(successRetList):
                            msg = f"\n{jd_pin}已组满"
                            logger.warning(msg)
                            Msg.append(msg)
                            return "已组满"
                        else:
                            need_num = (maxGroup - len(successRetList)) * 4
                            logger.warning(f'{jd_pin}组满还差{need_num}头')
                            return signUuid, secretPin, need_num
            else:
                logger.warning(f"{jd_pin}获取secretPin失败")
                return False
        else:
            logger.warning("IP可能黑了，请更换IP后重试")
            return False

    else:
        logger.warning(f"{jd_pin} 获取token失败")
        return False


@with_retries(max_tries=2, retries_sleep_second=0.5)
async def createam(cookie, proxies, session):
    try:
        jd_pin = unquote_plus(re.findall('pt_pin=(.*?);', cookie)[0])
        Team = wx_Team(cookie, proxies, session)
        token = await Team.get_token()
        if token:
            await Team.refreshcookie()
            await Team.getSimpleActInfoVo()
            secretPin = await Team.get_secretPin(token, venderId)
            res = await Team.saveCaptain(secretPin)
            # logger.warning(res)
            res_json = json.loads(res)
            if not res_json["result"]:
                res_json = json.loads(await Team.saveCaptain(secretPin))
                if '活动已结束' in res_json["errorMessage"]:
                    logger.warning(f'{jd_pin}建队失败： 活动已结束')
                    sys.exit()
                elif '抱歉您还不是店铺会员哦' in res_json["errorMessage"] or "活动仅限店铺会员参与哦" in res_json[
                    "errorMessage"]:
                    logger.warning(f'建队失败，未开卡，执行开卡')
                    message = await Team.bindWithVender()
                    if message:
                        await asyncio.sleep(0.8)
                        res = await Team.saveCaptain(secretPin)
                        res_json = json.loads(res)
                        if res_json["result"] == False:
                            if '活动已结束' in res_json["errorMessage"]:
                                logger.warning(f'活动已结束： {res_json["errorMessage"]}')
                                sys.exit()
                        if res_json["result"] == True:
                            signUuid = res_json["data"]["signUuid"]
                            # logger.warning(f"{jd_pin}建队成功\n队伍ID：{signUuid}")
                            return signUuid
                    else:
                        return False

            if res_json["result"] == True:
                signUuid = res_json["data"]["signUuid"]
                # logger.warning(f"{jd_pin}建队成功\n队伍ID：{signUuid}")
                return signUuid
        else:
            logger.warning(f"{jd_pin} 获取token失败")
            return False

    except Exception as e:
        logger.warning(f'建队失败: {e}')
        return False


@with_retries(max_tries=2, retries_sleep_second=0.5)
async def jointeam(cookie, signUuid, proxies, session):
    try:
        jd_pin = unquote_plus(re.findall('pt_pin=(.*?);', cookie)[0])
        Team = wx_Team(cookie, proxies, session)
        token = await Team.get_token()
        if token:
            await Team.refreshcookie()
            await Team.getSimpleActInfoVo()
            secretPin= await Team.get_secretPin(token, venderId)
            if secretPin != None:
                res = await Team.saveMember(signUuid, secretPin)
                # logger.warning(res)
                res_json = json.loads(res)
                if '抱歉您还不是店铺会员' in res or "活动仅限店铺会员参与哦" in res:
                    logger.warning(f"{jd_pin}未入会, 尝试入会！")
                    messge = await Team.bindWithVender()
                    if messge:
                        # logger.warning(result)
                        await asyncio.sleep(0.8)
                        res = await Team.saveMember(signUuid, secretPin)
                        res_json = json.loads(res)
                        if res_json["errorMessage"] != "":
                            if '活动已结束' in res_json["errorMessage"]:
                                logger.warning("活动已结束!")
                                return '活动已结束'
                            elif '满员了' in res_json["errorMessage"]:
                                logger.warning("该车队已满员，跳过执行")
                                return "该车队已满员，跳过执行"
                            else:
                                logger.warning(res_json["errorMessage"])
                                return False
                        elif res_json["data"][0]["nickName"]:
                            logger.warning(f'{jd_pin}加入{res_json["data"][0]["nickName"]}队伍成功')
                            neednums.append(jd_pin)
                    else:
                        return False
                elif res_json["errorMessage"] != "":
                    if '活动已结束' == res_json["errorMessage"]:
                        logger.warning("活动已结束!")
                        return '活动已结束'
                    elif '满员了' in res_json["errorMessage"]:
                        logger.warning("该车队已满员，跳过执行")
                        cookies.append(cookie)
                        return "该车队已满员，跳过执行"
                    else:
                        logger.warning(res_json["errorMessage"])
                        return False
                elif res_json["data"][0]["nickName"]:
                    logger.warning(f'{jd_pin}加入{res_json["data"][0]["nickName"]}队伍成功')
                    neednums.append(jd_pin)
        else:
            logger.warning(f"{jd_pin} 获取token失败")
    except Exception as e:
        logger.warning(f'入队失败: {e}')
        return '入队失败'


@with_retries(max_tries=2, retries_sleep_second=0.5)
async def get_teaminfo(cookie, proxies, session):  # 获取组队信息
    jd_pin = unquote_plus(re.findall('pt_pin=(.*?);', cookie)[0])
    Team = wx_Team(cookie, proxies, session)
    token = await Team.get_token()
    if token:
        await Team.refreshcookie()
        await Team.getSimpleActInfoVo()
        secretPin = await Team.get_secretPin(token, venderId)
        if secretPin != None:
            res_json = await Team.activityContent(secretPin)
            if res_json != None:
                successRetList = res_json["data"]["successRetList"]
                if maxGroup == len(successRetList):
                    logger.warning(f"账号{jd_pin} 已组满")
                    for i in successRetList:
                        msg = f'组员：{i["memberList"][0]["nickName"]}， {i["memberList"][1]["nickName"]}，{i["memberList"][2]["nickName"]}，{i["memberList"][3]["nickName"]}，{i["memberList"][4]["nickName"]}'
                        logger.warning(msg)
                        Msg.append(msg)

                elif len(successRetList) > 0:
                    logger.warning(f"账号{jd_pin} 已组{len(successRetList)}队")
                    for i in successRetList:
                        msg = f'组员：{i["memberList"][0]["nickName"]}， {i["memberList"][1]["nickName"]}，{i["memberList"][2]["nickName"]}，{i["memberList"][3]["nickName"]}, {i["memberList"][4]["nickName"]}'
                        logger.warning(msg)
                        Msg.append(msg)
                else:
                    msg = f"\n账号{jd_pin} 没有完成的组队"
                    logger.warning(msg)
                    Msg.append(msg)
    else:
        logger.warning(f"{jd_pin}获取token失败")


async def main():
    for cookie in capainters:
        jd_pin = unquote_plus(re.findall('pt_pin=(.*?);', cookie)[0])
        proxies =  await getproxy()
        Ac_data = await get_Actinfo(cookie, proxies)
        if Ac_data == "活动已结束!":
            break
        if Ac_data is False or Ac_data == '已组满':
            continue
        else:
            signUuid, secretPin, need_num = Ac_data[0], Ac_data[1], Ac_data[2]
            if need_num < Tuski_WX_TEAM_thread:
                excute_num = need_num
            else:
                excute_num = Tuski_WX_TEAM_thread
            if signUuid == "" or signUuid is None:
                jdtime_now = await jdtime()
                q, e = jdtime_now[0], jdtime_now[1]
                if startTime > q:
                    logger.warning('活动未开始，开始定时')
                    wait_time = startTime - q
                    if wait_time > 1800000:
                        msg= "\n活动未开始"
                        logger.warning(msg)
                        Msg.append(msg)
                        sys.exit()
                    else:
                        logger.warning(f'当前时间：{e}, {wait_time / 1000}秒之后执行组队')
                        time.sleep(wait_time / 1000)
                        jd_pin = re.findall('pt_pin=(.*?);', cookie)[0]
                        logger.warning(f'正在为{jd_pin}组队')
                        proxies = await getproxy()
                        signUuid = await createam(cookie, proxies)
                        if signUuid is False:
                            pass
                        else:
                            while True:
                                if len(cookies) == 0:
                                    logger.warning('没有cookie辣， 结束运行')
                                    return
                                k = 0
                                proxies = await getproxy()
                                for i in cookies[0:excute_num]:
                                    if k == 9:
                                        proxies = await getproxy()
                                    k += 1
                                    tasks.append(asyncio.create_task(jointeam(cookie=i, signUuid=signUuid, proxies = proxies)))
                                    cookies.remove(i)
                                done, _ = await asyncio.wait(tasks)
                                if '已结束' in str(done):
                                    return
                                if '已满员' in str(done):
                                    tasks.clear()
                                    break
                                tasks.clear()
                else:
                    signUuid = await createam(cookie, proxies)
                    if signUuid == False or signUuid is None or signUuid == '':
                        try:
                            signUuid, secretPin, pinImg = await get_Actinfo(cookie)
                            logger.warning(F"{jd_pin}队伍ID：signUuid")
                        except Exception as e:
                            logger.warning(e)
                            continue
                        while True:
                            if len(cookies) == 0:
                                logger.warning('没有cookie辣， 结束运行')
                                return
                            k = 0
                            proxies = await getproxy()
                            for i in cookies[0:excute_num]:
                                if k == 9:
                                    proxies = await getproxy()
                                k += 1
                                tasks.append(
                                    asyncio.create_task(jointeam(cookie=i, signUuid=signUuid, proxies=proxies)))
                                cookies.remove(i)
                            done, _ = await asyncio.wait(tasks)
                            if '已结束' in str(done):
                                return
                            if '已满员' in str(done):
                                tasks.clear()
                                break
                            tasks.clear()
                    else:
                        logger.warning(f"{jd_pin}队伍ID：{signUuid}")
                        while True:
                            if len(cookies) == 0:
                                logger.warning('没有cookie辣， 结束运行')
                                return
                            k = 0
                            proxies = await getproxy()
                            for i in cookies[0:excute_num]:
                                if k == 9:
                                    proxies = await getproxy()
                                k += 1
                                tasks.append(
                                    asyncio.create_task(jointeam(cookie=i, signUuid=signUuid, proxies=proxies)))
                                cookies.remove(i)
                            done, _ = await asyncio.wait(tasks)
                            if '已结束' in str(done):
                                return
                            if '已满员' in str(done):
                                tasks.clear()
                                break
                            tasks.clear()
            else:
                logger.warning(f"{jd_pin}队伍ID: {signUuid}")
                while True:
                    if len(cookies) == 0:
                        logger.warning('没有cookie辣， 结束运行')
                        return
                    k = 0
                    proxies = await getproxy()
                    for i in cookies[0:excute_num]:
                        if k == 9:
                            proxies = await getproxy()
                        k += 1
                        tasks.append(
                            asyncio.create_task(jointeam(cookie=i, signUuid=signUuid, proxies=proxies)))
                        cookies.remove(i)
                    done, _ = await asyncio.wait(tasks)
                    if '已满员' in str(done):
                        tasks.clear()
                        break
                    tasks.clear()
    symbo = ''
    send('兔斯基组队', symbo.join(Msg))

    

if __name__ == '__main__':
    try:
        ActivityUrl = os.environ.get("Tuski_WX_TEAM")
        host = re.findall('https?://((?:[\w-]+\.)+\w+(?::\d{1,5})?)', ActivityUrl)[0]
        activityId = re.findall('[0-9a-z]{32}', ActivityUrl)[0]
    except Exception as e:
        logger.warning("活动链接解析失败")
        sys.exit()
    try:
        cookies = getck()
    except Exception as e:
        logger.warning("获取cookie失败")
        sys.exit()
    try:
        Tuski_WX_TEAM_thread = int(os.environ.get("Tuski_WX_TEAM_thread"))
        logger.warning(f"当前并发数：{Tuski_WX_TEAM_thread}")
    except Exception as e:
        logger.warning("未设置线程数，默认并发4线程")
        Tuski_WX_TEAM_thread= 4
    try:
        Tuski_WX_TEAM_capainters = int(os.environ.get("Tuski_WX_TEAM_capainters"))
        logger.warning(f"当前车头数：{Tuski_WX_TEAM_capainters}")
    except Exception as e:
        logger.warning("未设置车头数，默认3车头")
        Tuski_WX_TEAM_capainters= 1
    try:
        Tuski_WX_TEAM_Proxy = os.environ.get("Tuski_WX_TEAM_Proxy")
        logger.warning(f"代理Url：{Tuski_WX_TEAM_Proxy}")
    except Exception as e:
        logger.warning("未设置代理")
    logger.warning("="*60)
    code = True
    stime = time.time()
    tasks = []
    neednums = []
    capainters = cookies[0:Tuski_WX_TEAM_capainters]
    asyncio.run(main())
    etime = time.time()
    logger.warning(f"本次运行耗费{etime - stime}秒")
