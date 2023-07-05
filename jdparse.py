# -*- coding: UTF-8 -*-
from time import time, strftime, localtime
import json,re,os,random
import httpx

# --------------------------------------------------------------------------------------------------
def get_jdck():
    url = 'http://c.athend.top:6700/open/auth/token?client_id=X8YwHPT-6nzn&client_secret=NrSTtEfri__Y9_bZjJC_Fxbz'
    res = json.loads(httpx.get(url=url).text)
    token = res["data"]["token"]
    token_type = res["data"]["token_type"]
    url = 'http://192.168.100.8:5700/open/envs'
    headers = {
        'Authorization': f'{token_type} {token}',
        'accept': 'application/json'
    }
    response = json.loads(httpx.get(url=url, headers=headers).text)
    cookies = []
    for i in response["data"]:
        if i["name"] == 'JD_COOKIE' and i["status"] == 0:
            cookies.append(i["value"])
        else:
            pass
    cookie = cookies[random.randint(0, len(cookies))]
    return cookie
#---------------------------------------口令解析--------------------------------------------------------
def jd_decode(code):
    s= httpx.Client()
    try:
        API = 'http://api.nolanstore.cc/JComExchange'
        code_data= json.loads(s.post(url= API, json={"code": f"{code}"}).text)
        print(code_data)
        title=code_data['data']['title']
        activityurl= code_data['data']['jumpUrl']
        # print(activityurl)
        return activityurl, title
    except Exception:
        return "我太菜了，解析不出来","none"

#---------------------------------------获取当前时间--------------------------------------------------------
# 获取当前时间
def get_time():
    time_now = round(time() * 1000)
    return time_now

#---------------------------------------pro邀请--------------------------------------------------------
def pro_parse(authorCode):
    s = httpx.Client()
    ck = get_jdck()
    t = get_time()
    body = {
        "code": authorCode,
        "_t": t
    }
    url = f"https://api.m.jd.com/api?client=&clientVersion=&appid=jdchoujiang_h5&t={t}&functionId=memberBringActPage&body={json.dumps(body)}&code={authorCode}&_t={t}"
    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9',
        'content-type': 'application/json',
        'cookie': ck,
        'origin': 'https://prodev.m.jd.com',
        'referer': 'https://prodev.m.jd.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'
    }
    try:
        response =s.request("GET", url, headers=headers).text
        url_data = json.loads(response)
        reward_detial = {
            'beginTime': strftime("%Y-%m-%d %H:%M:%S", localtime(url_data["data"]["beginTime"] / 1000)),
            'endTime': strftime("%Y-%m-%d %H:%M:%S", localtime(url_data["data"]["endTime"] / 1000)),
            'name': url_data["data"]["shopName"],  # 店铺名字
            'inviteFloor': url_data["data"]["inviteFloor"],  # 活动名称
            'rewards': {
                '0': {
                    'rewardName': url_data["data"]["rewards"][0]["rewardName"],
                    'inviteNum': url_data["data"]["rewards"][0]["inviteNum"],
                    'rewardStock': url_data["data"]["rewards"][0]["rewardStock"]
                },
                '1': {
                    'rewardName': url_data["data"]["rewards"][1]["rewardName"],
                    'inviteNum': url_data["data"]["rewards"][1]["inviteNum"],
                    'rewardStock': url_data["data"]["rewards"][1]["rewardStock"]
                },
                '2': {
                    'rewardName': url_data["data"]["rewards"][2]["rewardName"],
                    'inviteNum': url_data["data"]["rewards"][2]["inviteNum"],
                    'rewardStock': url_data["data"]["rewards"][2]["rewardStock"]
                }
            },  # 奖励明细
            'activtyURL': f'https://prodev.m.jd.com/mall/active/dVF7gQUVKyUcuSsVhuya5d2XD4F/index.html?code={authorCode}'
        }

        message = f"开始时间：{reward_detial['beginTime']}\n结束时间：{reward_detial['endTime']}\n店铺名称：{reward_detial['name']}\n邀请奖励:\n   邀请{reward_detial['rewards']['0']['inviteNum']}人 {reward_detial['rewards']['0']['rewardName']} 剩余：{reward_detial['rewards']['0']['rewardStock']} 份\n   邀请{reward_detial['rewards']['1']['inviteNum']}人 {reward_detial['rewards']['1']['rewardName']} 剩余：{reward_detial['rewards']['1']['rewardStock']}份\n   邀请{reward_detial['rewards']['2']['inviteNum']}人 {reward_detial['rewards']['2']['rewardName']} 剩余：{reward_detial['rewards']['2']['rewardStock']} 份  \n脚本规则: export prodevactCode=\"{authorCode}\"\n活动链接：{reward_detial['activtyURL']}"
        return message
    except Exception:
        return "获取活动信息出错"

#-------------------------------------无线类型解析----------------------------------------------------------
def decode_rule(code_url):
    try:
        if 'wxCollectionActivity' in code_url:
            text= f'加购有礼\n规则：\nexport M_WX_ADD_CART_URL="{code_url}"'
            return text
        elif 'wxDrawActivity' in code_url:
            text = f'幸运抽奖\n规则：\nexport M_WX_LUCK_DRAW_URL="{code_url}"'
            return text
        elif 'wxShopFollowActivity' in code_url:
            text = f'关注抽奖\n规则：\nexport M_WX_FOLLOW_DRAW_URL="{code_url}"'
            return text
        elif 'pointExgShiWu' in code_url:
            text = f'积分兑换实物\n规则：\nexport M_WX_POINT_DRAW_URL="{code_url}"'
            return text
        elif 'pointExgGift' in code_url:
            text = f'积分兑换礼品\n规则：\nexport M_WX_POINT_DRAW_URL="{code_url}"'
            return text
        elif 'wxFansInterActionActivity' in code_url:
            text = f'粉丝红包\n规则：\nexport M_WX_FANS_DRAW_URL="{code_url}"'
            return text
        elif 'wxBuildActivity' in code_url:
            text = f'盖楼领奖\n规则：\nexport M_WX_BUILD_DRAW_URL="{code_url}"'
            return text
        elif 'wxCartKoi' in code_url:
            text = f'购物车锦鲤\n规则：\nexport M_WX_CARTKOI_URL="{code_url}"'
            return text
        elif 'completeInfoActivity' in code_url:
            text = f'完善信息\n规则：\nM_WX_COMPLETE_DRAW_URL="{code_url}"'
            return text
        elif 'wxSecond' in code_url:
            text = f'读秒拼手速\n规则：\nexport M_WX_SECOND_DRAW_URL="{code_url}"'
            return text
        elif 'wxgame' in code_url:
            text = f'打豆豆\n规则：\nexport M_WX_DADOUDOU_URL="{code_url}"'
            return text
        elif 'wxGameActivity' in code_url:
            text = f'无线游戏\n规则：\nexport M_WX_GAME_URL="{code_url}"'
            return text
        elif 'wxShopGift' in code_url:
            text = f'店铺礼包\n规则：\nexport M_WX_SHOP_GIFT_URL="{code_url}"'
            return text
        elif 'wxMcLevelAndBirthGifts' in code_url:
            text = f'生日礼包\n规则：\nexport M_WX_LEVEL_BIRTH_URL="{code_url}"'
            return text
        elif 'wxTeam' in code_url:
            text = f'组队瓜分\n规则：\nexport M_WX_TEAM_URL="{code_url}"'
            return text
        elif  'interactsaas' in code_url:
            type = re.findall('activityType=([\w]{5})', code_url, re.S)[0]
            loreal_type = {
                '10023': {'name': '签到抽奖', 'script': 'export jd_loreal_Sign='},
                '10024': {'name': '加购有礼', 'script': 'export M_WX_ADD_CART_URL='},
                '10033': {'name': '组队瓜分', 'script': 'export ORGANIZE_TEAM_URL='},
                '10031': {'name': '幸运抽奖', 'script': 'export M_WX_LUCK_DRAW_URL='},
                '10053': {'name': '关注有礼', 'script': 'export jd_loreal_lkFollowShop='},
                '10063': {'name': '上上签抽奖', 'script': 'export jd_loreal_upperSign='},
                '10006': {'name': '邀请入会', 'script': 'export jd_loreal_inviteFollowShop='},
                '10070': {'name': '邀请入会', 'script': 'export jd_loreal_inviteFollowShop='},
                '10082': {'name': '积分抽奖', 'script': 'export M_WX_LUCK_DRAW_URL='},
                '10094': {'name': '游戏抽奖', 'script': 'export GAME_LUCK_DRAW_URL='},
                '10043': {'name': '分享有礼', 'script': 'export SHARE_POLITELY_URL='},
                '10052': {'name': '红包', 'script': 'export HBCOUNT_URL='},
                '10068': {'name': '邀请有礼', 'script': 'export INVITE_FOLLOW_SHOP_URL='},
                '10039': {'name': '知识超人', 'script': 'export KNOW_URL='},
                '10069': {'name': '关注有礼', 'script': 'export LKFOLLOW_SHOP_URL='},
            }
            try:
                activity_type = loreal_type[type]
            except Exception:
                return "无法匹配无线规则"
            else:
                replytext = f"活动类型：{activity_type['name']}\n规则：\n{activity_type['script']}\"{code_url}\""
                return replytext
    except:
            return "无法匹配无线规则"

def parse(text):
    if 'https://pro.m.jd.com' in text or 'https://prodev.m.jd.com' in text:
        try:
            authorCode = re.findall('code=([0-9a-z]{10,})', text)[0]
        except:
            replytext=f"活动链接：{text}\n无法解析"
            return replytext
        # print(authorCode)
        replytext = pro_parse(authorCode)
        return replytext
    elif 'cjhy-isv.isvjcloud' in text or 'lzkj-isv.isvjcloud' in text:
        activityurl = re.findall('https://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]', text)[0]
        replytext = decode_rule(activityurl)
        return replytext
    else:
        try:
            decode_data = jd_decode(text)
            acurl , ac_title = str(decode_data[0]), decode_data[1]
        except:
            replytext=f'解析失败，请回复要解析的口令或回复一条消息'
            return replytext
        else:
            if acurl != '我太菜了，解析不出来':
                if 'https://pro.m.jd.com'in acurl or 'https://prodev.m.jd.com' in acurl:
                    try:
                        authorCode = re.findall('code=([0-9a-z]{10,})', acurl)[0]
                    except:
                        if "inviter=" in acurl:
                            invitercode = re.findall('inviter=(.*?)&', acurl)[0]
                            repley_text=f"{ac_title}\n活动链接：{acurl}\n助力码：\n{invitercode}"
                            return repley_text
                        else:
                            repleytext= f"活动链接：{acurl}\n{ac_title}"
                            return repleytext
                    else:
                        r_text = pro_parse(authorCode)
                        replytext=f'{ac_title}\n{r_text}'
                        return replytext
                elif 'https://cjhy-isv.isvjcloud.com' in acurl or 'https://lzkj-isv.isvjcloud.com' in acurl:
                    replytext = decode_rule(acurl)
                    replytext=f'{ac_title}\n{replytext}'
                    return replytext
                elif "shareId=" in acurl:
                    zhulima = re.findall("shareId=(.*?)&", acurl)[0]
                    print(zhulima)
                    r_text = f'活动链接：{acurl}\n助力码： {zhulima}'
                    replytext=f'{ac_title}\n{r_text}'
                    return replytext
                elif "inviter_id=" in acurl:
                    zhulima = re.findall("inviter_id=(.*?)&", acurl)[0]
                    print(zhulima)
                    r_text = f'活动链接：{acurl}\n助力码： {zhulima}'
                    replytext=f'{ac_title}\n{r_text}'
                    return replytext
                else:
                    r_text = acurl
                    replytext=f'{ac_title}\n{r_text}'
                    return replytext
            else:
                replytext = f'{acurl}'
                return replytext


res= parse('10:/打开京东，组队分积分，这样的好事我是不会忘了你的，赶快来参加，就差你了！！E6n1Y3ET51！⇢倞◕Dσσōng')
print(res)
