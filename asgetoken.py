import asyncio
import json,re
import aiohttp
import aiofiles
import time,os

async def getoken(cookie,functionId,body):
    jd_pin = re.findall('pt_pin=(.*?);', cookie)[0]
    async def get_token():
        async with aiohttp.ClientSession() as s:
            api = "http://192.168.100.8:9090/api/jdsign"
            sign_data ={
                "fn":functionId,
                "body":body
            }
            response= await s.post(url=api, json=sign_data)
            # print(response)
            res_json=await response.json()
            # print(res_json)
            url= f'https://api.m.jd.com/client.action?functionId={functionId}&{res_json["body"]}'
            # print(url)
            headers = {
                "User-Agent": "jdapp;android;11.2.8;;;Mozilla/5.0 (Linux; Android 10; ONEPLUS A5010 Build/QKQ1.191014.012; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/76.0.3809.89 MQQBrowser/6.2 TBS/045230 Mobile Safari/537.36",
                'Cookie': cookie
            }
            response=await s.get(url,headers=headers)
            text_data=await response.text()
            #print(text_data)
            token = re.findall('"token":"(.*?)"}$',text_data)[0]
            #print(token)
            return token

    if os.path.exists('cache/tokens.json'):
        with open("cache/tokens.json", "r", encoding="utf-8") as f:
            tokens= json.load(f)
    else:
        tokens = {}
    if jd_pin in tokens:
        if tokens[jd_pin]["Expiredtime"] > int(time.time()):
            return tokens[jd_pin]["token"]
        else:
            token= await get_token()
            Expired_time= int(time.time()) + 840
            tokens[jd_pin]= {"token":token, "Expiredtime": Expired_time}
            async with aiofiles.open("cache/tokens.json", "w", encoding="utf-8") as f:
                await f.write(json.dumps(tokens, indent=4, ensure_ascii=False))
            return token
    else:
        token = await get_token()
        Expiredtime = int(time.time()) + 840
        tokens[jd_pin] = {"token": token, "Expiredtime": Expiredtime}
        async with aiofiles.open("cache/tokens.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps(tokens, indent=4, ensure_ascii=False))
        return token
