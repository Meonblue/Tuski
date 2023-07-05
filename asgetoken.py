import asyncio
import json,re
import aiohttp
import aiofiles
import time

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
                'Connection': 'keep-alive',
                'Accept-Encoding': 'gzip, deflate, br',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                "User-Agent": "jdapp;android;11.2.8;;;Mozilla/5.0 (Linux; Android 10; ONEPLUS A5010 Build/QKQ1.191014.012; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/76.0.3809.89 MQQBrowser/6.2 TBS/045230 Mobile Safari/537.36",
                'Cookie': cookie,
                'Accept-Language': 'zh-Hans-CN;q=1 en-CN;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
            }
            response=await s.get(url,headers=headers)
            text_data=await response.text()
            #print(text_data)
            token = re.findall('"token":"(.*?)"}$',text_data)[0]
            #print(token)
            return token

    with open("tokens.json", "r", encoding="utf-8") as f:
        tokens= json.load(f)
    if jd_pin in tokens:
        if tokens[jd_pin]["Expiredtime"] > int(time.time()):
            return tokens[jd_pin]["token"]
        else:
            token= await get_token()
            Expired_time= int(time.time()) + 840
            tokens[jd_pin]= {"token":token, "Expiredtime": Expired_time}
            with open("tokens.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(tokens, indent=4, ensure_ascii=False))
            return token
    else:
        token = await get_token()
        Expiredtime = int(time.time()) + 840
        tokens[jd_pin] = {"token": token, "Expiredtime": Expiredtime}
        with open("tokens.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(tokens, indent=4, ensure_ascii=False))
        return token

'''async def main():
    ck= 'pt_key=app_openAAJkf8iGADDbf0O2qh45NrW53eRi7DdHbAEXx9482k4vfIeotyb1u5CfYfIXzUc9Bg5TVkFxZm0;pt_pin=jd_64bfef0cd8500;'
    function = 'isvObfuscator'
    body = {"url": "https://cjhy-isv.isvjcloud.com", "id": ""}
    token = await getoken(ck, functionId=function, body=body)
    print(token)

asyncio.run(main())'''