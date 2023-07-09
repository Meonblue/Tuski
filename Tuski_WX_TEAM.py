#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lz，cj无线组队脚本  BY.Tuski
版本： 2.0
环境变量 活动url： export Tuski_WX_TEAM="活动url"
        线程数： Tuski_WX_TEAM_thread 如未设置默认4线程
        车头数： Tuski_WX_TEAM_capainters 如未设置默认3车头
        代理：Tuski_WX_TEAM_proxy 如未设置默认3车头
TG: https://t.me/cooooooCC
new Env('Tuski_组队');
禁用就行 Tuski_WX_TEAM.py
"""

import asyncio
import aiohttp, requests
import json, re, os, sys, time
from asgetoken import getoken
from urllib.parse import quote_plus, unquote_plus
import threading
import telnetlib
from Get_cookies import getck
from sendNotify import send
from session import with_retries



def getproxy():
    global proxies,get_proxy_time,IP,port
    if Tuski_WX_TEAM_Proxy == None:
        proxies = None
        return None
    s = requests.session()
    # 底下 s.get之后的链接为代理链接 自备
    response = s.get(Tuski_WX_TEAM_Proxy)
    res = response.text

    try:
        IP= re.findall('(?:(?:2(?:5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(?:\.(?:(?:2(?:5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}', res)[0]
        port = re.findall(":([0-9]+)", res)[0]
        proxies = f"http://{IP}:{port}"
        print(f'当前设置代理：{proxies}')
        s.close()
        return proxies
    except:
        print('获取代理失败')
        proxies = None
        s.close()
        return None
        # sys.exit()

def checkproxy():
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
                            print("代理IP有效！")
                            time.sleep(3)
                            retrys = 0
                        except:
                            retrys += 1
                            print(f"代理IP失效！第{retrys}次重试")
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
        # print('')
        raise TimeoutError("IP可能黑了，请更换IP后重试")
    else:
        pass


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
            if host in ["cjhy-isv.isvjcloud.com", "cjhydz-isv.isvjcloud.com"]:
                if '+' in secretPin:
                    secretPin = quote_plus(secretPin)
            secretPin = quote_plus(secretPin)
            return secretPin
        else:
            print("获取ping失败")
            return False
    else:
        print("获取ping失败")
        return False


async def activityContent(secretPin, session: aiohttp.ClientSession):  # 获取活动的信息
    url = f'https://{host}/wxTeam/activityContent'
    data= f"activityId={activityId}&pin={secretPin}&signUuid="
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
            return text
    else:
        return False


async def saveCaptain(secretPin,session: aiohttp.ClientSession):  # 建队
    url = f'https://{host}/wxTeam/saveCaptain?activityId={activityId}&pin={secretPin}&pinImg=&venderId={venderId}'
    # data = f"activityId={activityId}&pin={secretPin}&pinImg=&venderId={venderId}"
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
    t = 0
    while t < 3:
        res = await session.post(url, headers=haeders,proxy=proxies)
        if res.status == 200:
            return await res.text()
        else:
            t += 1
            print(f'第{t}次建队失败')
    else:
        print(f"建队重试大于三次，跳过此ck")
        return False


async def saveMember(signUuid, secretPin,session):  # 加入队伍
    url = f'https://{host}/wxTeam/saveMember?activityId={activityId}&signUuid={signUuid}&pin={secretPin}&pinImg=&venderId={venderId}'
    # data =f"activityId={activityId}&signUuid={signUuid}&pin={secretPin}&pinImg=&venderId={venderId}"
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
    t = 0
    while t < 2:
        res = await session.post(url, headers=haeders, proxy=proxies)
        if res.status == 200:
            text = await res.text()
            return text
        else:
            t += 1
            print(f'第{t}次组队失败')
    else:
        print(f"组队重试大于三次，跳过此ck")
        return False


async def bindWithVender(cookie, session: aiohttp.ClientSession):
    try:
        headers = {
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'User-Agent': ua,
            'Cookie': cookie,
            'Host': 'api.m.jd.com',
            'Referer': 'https://shopmember.m.jd.com/',
            'Accept-Language': 'zh-Hans-CN;q=1 en-CN;q=0.9',
            'Accept': '*/*'
        }
        params = {
            'appid': 'jd_shop_member',
            'functionId': 'bindWithVender',
            'body': json.dumps({
                'venderId': venderId,
                'shopId': shopId,
                'bindByVerifyCodeFlag': 1
            }, separators=(',', ':'))
        }
        res = await session.post('https://api.m.jd.com/', headers=headers, params=params, proxy=proxies)
        text = await res.text()
        res_json = json.loads(text)
        if res_json['success']:
            return res_json['message']
    except Exception as e:
        print(e)
        return False

@with_retries(max_tries=2, retries_sleep_second=0.5)
async def get_teaminfo(ck, session: aiohttp.ClientSession):
        jd_pin = re.findall('pt_pin=(.*?);', ck)[0]
        token = await get_token(ck)
        await refreshck(session)
        await getSimpleActInfoVo(session)
        secretPin= await getping(token, session)
        res_json = await activityContent(secretPin, session)
        if res_json != False:
            successRetList = res_json["data"]["successRetList"]
            if maxGroup == len(successRetList):
                print(f"账号{jd_pin} 已组满")
                for i in successRetList:
                    Msg= f'组员：{i["memberList"][0]["nickName"]}， {i["memberList"][1]["nickName"]}，{i["memberList"][2]["nickName"]}，{i["memberList"][3]["nickName"]}，{i["memberList"][4]["nickName"]}'
                    print(Msg)
                    Message += Msg
            elif len(successRetList) > 0:
                print(f"账号{jd_pin} 已组{len(successRetList)}队")
                for i in successRetList:
                    Msg= f'组员：{i["memberList"][0]["nickName"]}， {i["memberList"][1]["nickName"]}，{i["memberList"][2]["nickName"]}，{i["memberList"][3]["nickName"]}, {i["memberList"][4]["nickName"]}'
                    print(Msg)
                    Message += Msg
            else:
                print(f"账号{jd_pin} 没有完成的组队")


@with_retries(max_tries=2, retries_sleep_second=0.5)
async def get_ACinfo(cookie, session: aiohttp.ClientSession):
    global code,Message
    Message=''
    jd_pin = re.findall('pt_pin=(.*?);', cookie)[0]
    token = await get_token(cookie)
    await refreshck(session)
    await getSimpleActInfoVo(session)
    secretPin= await getping(token, session)
    res_json = await activityContent(secretPin, session)
    # print(res_json)
    if res_json != False:
        global maxGroup, startTime, endTime
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
            shopName = await shopinfo(session)
            cookies.remove(cookies[0])
            cookies.insert(maxGroup * 4 + 3, capainters[0])
            if shopName != False:
                Msg= f'🐹🐹 -- 当前奖励详情 -- 🐽🐽\n店铺：{shopName}\n 活动链接：{activityUrl}\n活动名称:{actName}\n活动明细:\n{rulers}'
                print(Msg)
                Message += Msg
            else:
                Msg = f'🐹🐹 -- 当前奖励详情 -- 🐽🐽\n店铺：{shopName}\n 活动链接：{activityUrl}\n活动名称:{actName}\n活动明细:\n{rulers}'
                print(Msg)
                Message += Msg
                print()
            if successRetList == None:
                print(f"{jd_pin} 未开始组队")
                need_num= maxGroup * 4
                return signUuid, secretPin, need_num
            elif maxGroup == len(successRetList):
                print(f'{jd_pin} 已组满')
                return '已组满'
            else:
                need_num = (maxGroup - len(successRetList)) * 4
                return signUuid, secretPin, need_num
        else:
            if successRetList == None:
                print(f"{jd_pin} 未开始组队")
                need_num = maxGroup * 4
                return signUuid, secretPin, need_num
            elif maxGroup == len(successRetList):
                print(f'{jd_pin} 已组满')
                return '已组满'
            else:
                need_num = (maxGroup - len(successRetList)) * 4
                return signUuid, secretPin, need_num
    else:
        print("获取活动信息失败")
        return False


@with_retries(max_tries=2, retries_sleep_second=0.5)
async def createam(cookie, session: aiohttp.ClientSession):
    try:
        jd_pin = re.findall('pt_pin=(.*?);', cookie)[0]
        token = await get_token(cookie)
        if token == False:
            return False
        await refreshck(session)
        await getSimpleActInfoVo(session)
        secretPin= await getping(token, session)
        res = await saveCaptain(secretPin, session)
        # print(res)
        res_json = json.loads(res)
        if res_json["result"] == False:
            res_json = json.loads(await saveCaptain(secretPin,session))
            if '活动已结束' in res_json["errorMessage"]:
                print(f'{jd_pin}建队失败： 活动已结束')
                sys.exit()
            elif '抱歉您还不是店铺会员哦' in res_json["errorMessage"] or "活动仅限店铺会员参与哦" in res_json["errorMessage"]:
                print(f'舰队失败，未开卡，执行开卡')
                message = await bindWithVender(cookie, session)
                if '成功' in message:
                    print(message)
                    res = await saveCaptain(secretPin,session)
                    res_json = json.loads(res)
                    if res_json["result"] == False:
                        if '活动已结束' in res_json["errorMessage"]:
                            print(f'活动已结束： {res_json["errorMessage"]}')
                            sys.exit()
                    if res_json["result"] == True:
                        signUuid = res_json["data"]["signUuid"]
                        # print(f"{jd_pin}建队成功\n队伍ID：{signUuid}")
                        return signUuid
                else:
                    print("入会失败")
                    raise RuntimeError("入会失败")
        if res_json["result"] == True:
            signUuid = res_json["data"]["signUuid"]
            # print(f"{jd_pin}建队成功\n队伍ID：{signUuid}")
            return signUuid
    except Exception as e:
        print(f'建队失败: {e}')
        return False


@with_retries(max_tries=2, retries_sleep_second=0.5)
async def jointeam(cookie, signUuid, session: aiohttp.ClientSession):
    try:
        token = await get_token(cookie)
        if token == False:
            return False
        jd_pin = re.findall('pt_pin=(.*?);', cookie)[0]
        await refreshck(session)
        await getSimpleActInfoVo(session)
        secretPin= await getping(token, session)
        if secretPin == False:
            print(f'账号{jd_pin}获取pin失败')
            return False
        else:
            res = await saveMember(signUuid, secretPin,session)
            # print(res)
            res_json = json.loads(res)
            if '抱歉您还不是店铺会员' in res or "活动仅限店铺会员参与哦" in res:
                print(f"您还不是店铺会员, 尝试入会")
                result = await bindWithVender(cookie, session)
                if result != False:
                    # print(result)
                    res = await saveMember(signUuid, secretPin, session)
                    res_json = json.loads(res)
                    if res_json["errorMessage"] != "":
                        if '活动已结束' in res_json["errorMessage"]:
                            print("活动已结束!")
                            return '活动已结束'
                        elif '满员了' in res_json["errorMessage"]:
                            print("该车队已满员，跳过执行")
                            return "该车队已满员，跳过执行"
                        else:
                            print(res_json["errorMessage"])
                            return False
                    elif res_json["data"][0]["nickName"]:
                        print(f'加入{res_json["data"][0]["nickName"]}队伍成功')
                        neednums.append(jd_pin)
                else:
                    print("入会失败")
                    return False
            elif res_json["errorMessage"] != "":
                if '活动已结束' == res_json["errorMessage"]:
                    print("活动已结束!")
                    return '活动已结束'
                elif '满员了' in res_json["errorMessage"]:
                    print("该车队已满员，跳过执行")
                    cookies.append(cookie)
                    return "该车队已满员，跳过执行"
                else:
                    print(res_json["errorMessage"])
                    return False
            elif res_json["data"][0]["nickName"]:
                print(f'加入{res_json["data"][0]["nickName"]}队伍成功')
                neednums.append(jd_pin)
    except Exception as e:
        print(f'入队失败: {e}')
        return '入队失败'


async def main():
    if Tuski_WX_TEAM_Proxy == "None":
        pass
    else:
        thread.start()
        await asyncio.sleep(0.5)
    for cookie in capainters:
        jd_pin = re.findall('pt_pin=(.*?);', cookie)[0]
        Ac_data = await get_ACinfo(cookie=cookie)
        if Ac_data == False or Ac_data == '已组满':
            continue
        else:
            signUuid, secretPin, need_num = Ac_data[0], Ac_data[1], Ac_data[2]
            if need_num < Tuski_WX_TEAM_thread:
                excute_num = need_num
            else:
                excute_num= Tuski_WX_TEAM_thread
            if signUuid == '' or signUuid is None:
                print(f'{jd_pin}组满还差{need_num}头')
                jdtime_now = await jdtime()
                q, e = jdtime_now[0], jdtime_now[1]
                if endTime < q:
                    print("活动已结束!")
                    sys.exit()
                else:
                    if startTime > q:
                        print('活动未开始，开始定时')
                        wait_time = startTime - q
                        if wait_time > 1800000:
                            print(f'距离活动开始时间大于半小时，退出执行')
                            sys.exit()
                        else:
                            print(f'当前时间：{e}, {wait_time / 1000}秒之后执行组队')
                            code = False
                            time.sleep(wait_time / 1000)
                            getproxy()
                            code= True
                            jd_pin = re.findall('pt_pin=(.*?);', cookie)[0]
                            print(f'正在为{jd_pin}组队')
                            signUuid = await createam(cookie)
                            if signUuid == False or signUuid is None or signUuid == '':
                                pass
                            else:
                                while True:
                                    if len(cookies) == 0:
                                        print('没有ck辣， 结束运行')
                                        return
                                    for i in cookies[0:excute_num]:
                                        tasks.append(asyncio.create_task(jointeam(cookie=i, signUuid=signUuid)))
                                        cookies.remove(i)
                                    done, _ = await asyncio.wait(tasks)
                                    if '已结束' in str(done):
                                        code = False
                                        return
                                    if '已满员' in str(done):
                                        tasks.clear()
                                        break
                                    tasks.clear()
                    else:
                        print(F"{jd_pin}尚未组队")
                        signUuid = await createam(cookie)
                        if signUuid == False or signUuid is None or signUuid == '':
                            try:
                                signUuid, secretPin, pinImg = await get_ACinfo(cookie)
                                print(F"{jd_pin}队伍ID：signUuid")
                            except Exception as e:
                                print(e)
                                continue
                            while True:
                                if len(cookies) == 0:
                                    print('没有ck辣， 结束运行')
                                    return
                                for i in cookies[0:excute_num]:
                                    tasks.append(asyncio.create_task(jointeam(cookie=i, signUuid=signUuid)))
                                    cookies.remove(i)
                                done, _ = await asyncio.wait(tasks)
                                if '已结束' in str(done):
                                    code = False
                                    return
                                if '已满员' in str(done):
                                    tasks.clear()
                                    break
                                tasks.clear()
                        else:
                            print(f"{jd_pin}队伍ID：{signUuid}")
                            while True:
                                if len(cookies) == 0:
                                    print('没有ck辣， 结束运行')
                                    return
                                for i in cookies[0:excute_num]:
                                    tasks.append(asyncio.create_task(jointeam(cookie=i, signUuid=signUuid)))
                                    cookies.remove(i)
                                done, _ = await asyncio.wait(tasks)
                                if '已结束' in str(done):
                                    code = False
                                    return
                                if '已满员' in str(done):
                                    tasks.clear()
                                    break
                                tasks.clear()
            else:
                print(f"{jd_pin}队伍ID: {signUuid}")
                while True:
                    if len(cookies) == 0:
                        print('没有ck辣， 结束运行')
                        return
                    for i in cookies[0:excute_num]:
                        tasks.append(asyncio.create_task(jointeam(cookie=i, signUuid=signUuid)))
                        cookies.remove(i)
                    done= await asyncio.wait(tasks)
                    if '已结束' in str(done):
                        code = False
                        return
                    if '已满员' in str(done):
                        tasks.clear()
                        break
                    tasks.clear()
    send('兔斯基组队', Message)


if __name__ == '__main__':
    ua = 'jdapp;android;10.4.0;10;network/wifi;Mozilla/5.0 (Linux; Android 11; MI 8 Build/QKQ1.190828.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/77.0.3865.120 MQQBrowser/6.2 TBS/045227 Mobile Safari/537.36'
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
        Tuski_WX_TEAM_thread = int(os.environ.get("Tuski_WX_TEAM_thread"))
        print(f"当前并发数：{Tuski_WX_TEAM_thread}")
    except Exception as e:
        print("未设置线程数，默认并发4线程")
        Tuski_WX_TEAM_thread= 4
    try:
        Tuski_WX_TEAM_capainters = int(os.environ.get("Tuski_WX_TEAM_capainters"))
        print(f"当前车头数：{Tuski_WX_TEAM_capainters}")
    except Exception as e:
        print("未设置车头数，默认3车头")
        Tuski_WX_TEAM_capainters= 3
    try:
        Tuski_WX_TEAM_Proxy = os.environ.get("Tuski_WX_TEAM_Proxy")
        print(f"代理Url：{Tuski_WX_TEAM_Proxy}")
    except Exception as e:
        print("未设置代理")
        Tuski_WX_TEAM_Proxy= None
    print("="*60)
    code = True
    stime = time.time()
    thread = threading.Thread(target=getproxy, name="获取代理")
    host = re.findall('https?://((?:[\w-]+\.)+\w+(?::\d{1,5})?)', activityUrl)[0]
    # print(host)
    activityId = re.findall('[0-9a-z]{32}', activityUrl)[0]
    tasks = []
    neednums = []
    capainters = cookies[0:Tuski_WX_TEAM_capainters]
    asyncio.run(main())
    etime = time.time()
    print(f"本次运行耗费{etime - stime}秒")
    for ck in capainters:
        asyncio.run(get_teaminfo(ck))
