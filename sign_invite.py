# -*- coding: utf-8 -*-
import requests
from datetime import datetime
import time
import json
# wps ID列表，需要做任务的账号ID，可以添加多个

# 企业微信信息，用于推送消息通知，以查看执行情况

# 微信推送
def push_wechat(txt):
    # get access_token
    token_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s' % (qywx_info['corid'], qywx_info['secret'])
    r = requests.get(token_url).json()
    assert r['errcode'] == 0, r['errmsg']
    # push
    push_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + r['access_token']
    jsondata = {
       "touser" : '@all',
       "msgtype" : "text",
       "agentid" : qywx_info['agentid'],
       "text" : {
           "content" : txt
       }
    }
    r = requests.post(push_url, json = jsondata).json()
    print('push succeed!' if r['errcode'] == 0 else 'push failed! ' + r['errmsg'])

# 主函数
def main():
    # 被邀请人的 wps_sid 列表，
    sid_list = [
        "V02StVuaNcoKrZ3BuvJQ1FcFS_xnG2k00af250d4002664c02f",
        "V02SWIvKWYijG6Rggo4m0xvDKj1m7ew00a8e26d3002508b828",
        "V02Sr3nJ9IicoHWfeyQLiXgvrRpje6E00a240b890023270f97",
        "V02SBsNOf4sJZNFo4jOHdgHg7-2Tn1s00a338776000b669579",
        "V02S2oI49T-Jp0_zJKZ5U38dIUSIl8Q00aa679530026780e96",
        "V02ShotJqqiWyubCX0VWTlcbgcHqtSQ00a45564e002678124c",
        "V02SFiqdXRGnH5oAV2FmDDulZyGDL3M00a61660c0026781be1",
        "V02S7tldy5ltYcikCzJ8PJQDSy_ElEs00a327c3c0026782526",
        "V02SPoOluAnWda0dTBYTXpdetS97tyI00a16135e002684bb5c",
        "V02Sb8gxW2inr6IDYrdHK_ywJnayd6s00ab7472b0026849b17",
        "V02SwV15KQ_8n6brU98_2kLnnFUDUOw00adf3fda0026934a7f",
        "V02SC1mOHS0RiUBxeoA8NTliH2h2NGc00a803c35002693584d"

    ]
    s = requests.session()
    invite_url = 'http://zt.wps.cn/2018/clock_in/api/invite'
    for user_id in id_list:
        post_data = {'invite_userid': user_id}
        count = {'total':0, 'succ':0, 'fail':[]}
        for wps_sid in sid_list:
            r = s.post(invite_url, headers = {'sid': wps_sid}, data = post_data)
            # debug
            print(r.text)
            count['total'] += 1
            try:
                rjson = r.json()
                if rjson['result'] == 'ok':
                    count['succ'] += 1
                elif rjson['result'] == 'error':
                    count['fail'].append({'sid':wps_sid[:6]+'***'+wps_sid[-4:], 'msg':rjson['msg']})
            except json.JSONDecodeError:
                count['fail'].append({'sid':wps_sid[:6]+'***'+wps_sid[-4:], 'msg':'unknown error'})  
            if count["succ"] >= 10 or wps_sid is sid_list[-1]:
                break
            time.sleep(2.5) # 间隔2.5秒再邀请
            
        push_txt = datetime.today().isoformat(sep=' ', timespec='seconds')
        push_txt += "\nWPS签到的邀请推送"
        push_txt += "\n尝试为【ID：%d】邀请 %d 位用户，其中：" % (user_id, count['total'])
        push_txt += "\n邀请成功 %d 人，失败 %d 人。" % (count['succ'], len(count['fail']))
        for errItem in count['fail']:
            push_txt += '\n%s, %s' % (errItem['sid'], errItem['msg'])
        push_txt += '\n<a href="mp://F49Xy9rxwhOWm8o">点我去打卡</a>'
        push_wechat(push_txt)
        
def main_handler(event, context):
    return main()

if __name__ == '__main__':
    main()
