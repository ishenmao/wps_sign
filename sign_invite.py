# -*- coding: utf-8 -*-
import requests
import datetime
import time
import json
import sys
# wps ID列表，需要做任务的账号ID，可以添加多个
id_list = []

# 企业微信信息，用于推送消息通知，以查看执行情况
qywx_info = {
    # 企业 ID
    'corid' : '企业 ID',
    # 应用密钥
    'secret' : '应用密钥',
    # 应用 ID
    'agentid' : 123456
}
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
    "V02Sw9-goMQAxyEQu_EULMetb-INZo000af1142c00479959d8",
    "V02S0R96lUd8ZEzQtyjxZX-kHQ2_tpk00a28f1650047c345ee",
    "V02SBxbHOhf4rcYlBaXzTfJ8WC3B6PE00aa5f34d0038de5bac",
    "V02SRvwTFf68enT4JrOPhQkKrKKqv5k00ab38f8500380673c8",
    "V02SS1Aj322-C9Z-P36iZF2epL78zOQ00a7ea26400300425d3",
    "V02S96aSosktKJiRKwEwBhqiWKHhxkE00a01300600374985fe",
    "V02SFiqdXRGnH5oAV2FmDDulZyGDL3M00a61660c0026781be1",
    "V02SzpPttrDh9DtVZZjuSixmKOYsAuU00a98ee4a0047756591",
    "V02SkTszoOYP88gtXvH1cXoDrMGoEGg00af1f571004626b252",
    "V02SEdbqgnwva8UpfFOiw5BmksbY_JY00a53a2c300461f24f7",
    "V02S6UQdQhot5IO9pmvBnEuiiVGcCYU00a6bc19c0047b369fa",

    ]
    s = requests.session()
    invite_url = 'http://zt.wps.cn/2018/clock_in/api/invite'
    for user_id in id_list:
        post_data = {'invite_userid': user_id,"client_code": "040ce6c23213494c8de9653e0074YX30", "client": "alipay"}
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
            time.sleep(10) # 间隔2.5秒再邀请
            
        push_txt = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).isoformat(sep=' ', timespec='seconds')
        push_txt += "\nWPS签到的邀请推送"
        push_txt += "\n尝试为【ID：%d】邀请 %d 位用户，其中：" % (user_id, count['total'])
        push_txt += "\n邀请成功 %d 人，失败 %d 人。" % (count['succ'], len(count['fail']))
        for errItem in count['fail']:
            push_txt += '\n%s, %s' % (errItem['sid'], errItem['msg'])
        push_txt += '\n<a href="mp://F49Xy9rxwhOWm8o">会员打卡</a>'
        push_txt += '   <a href="mp://P2tulcSBYclooSc">稻壳签到</a>'
        push_txt += '   <a href="https://zt.wps.cn/spa/2019/vip_mobile_sign_v2/?from=wx_info_page&_wxv=20210302">积分签到</a>'
        push_wechat(push_txt)
        
def main_handler(event, context):
    return main()
def get_args():
    assert len(sys.argv) == 5, '参数个数不对'
    for item_id in sys.argv[1].split(','):
        id_list.append(int(item_id))
    qywx_info['corid'] = sys.argv[2]
    qywx_info['secret'] = sys.argv[3]
    qywx_info['agentid'] = int(sys.argv[4])
    
if __name__ == '__main__':
    """
    for a in sys.argv:
        print("fuck:   ", a)
    """
    get_args()
    main()
