import json, re
import aiohttp
import time, os
from fake_useragent import UserAgent
from urllib.parse import unquote_plus
from session import with_retries


@with_retries(max_tries=2, retries_sleep_second=1)
async def getoken(cookie, functionId, body, proxies, session: aiohttp.ClientSession):
    jd_pin = unquote_plus(re.findall('pt_pin=(.*?);', cookie)[0])
    UA = UserAgent().random
    async def get_token():
        try:
            api = "http://192.168.100.8:9090/api/jdsign"
            sign_data = {
                "fn": functionId,
                "body": body
            }
            response = await session.post(url=api, json=sign_data)
            # print(response.status)
            res_json = await response.json()
            # print(res_json)
            url = f'https://api.m.jd.com/client.action?functionId={functionId}&{res_json["body"]}'
            # print(url)
            headers = {
                "User-Agent": UA,
                'Cookie': cookie
            }
            response = await session.get(url, headers=headers, proxy= proxies)
            text_data = await response.text()
            # print(text_data)
            token = re.findall('"token":"(.*?)"}$', text_data)[0]
            # print(token)
            return token
        except Exception as e:
            return False

    try:
        if os.path.exists('cache/tokens.json'):
            with open("cache/tokens.json", "r", encoding="utf-8") as f:
                tokens = json.load(f)
        else:
            tokens = {}
    except Exception as e:
        tokens = {}

    if jd_pin in tokens:
        if tokens[jd_pin]["Expiredtime"] > int(time.time()):
            return tokens[jd_pin]["token"]
        else:
            token = await get_token()
            if token == False:
                return False
            Expired_time = int(time.time()) + 840
            tokens[jd_pin] = {"token": token, "Expiredtime": Expired_time}
            with open("cache/tokens.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(tokens, indent=4, ensure_ascii=False))
            return token

    else:
        token = await get_token()
        if token == False:
            return False

        Expiredtime = int(time.time()) + 840
        tokens[jd_pin] = {"token": token, "Expiredtime": Expiredtime}
        with open("cache/tokens.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(tokens, indent=4, ensure_ascii=False))
        return token
