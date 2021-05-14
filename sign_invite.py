# -*- coding: utf-8 -*-
import requests
import datetime
import time
import json
import sys

dlabel = 1
def debugme(other = None):
    global dlabel
    print('【%s】' % str(dlabel), other)
    dlabel += 1



# wps ID
user_id = ''
sid_list = []
client = {}
qywx_info = {}
user_sid = ''
qlist = []
# 微信推送


def push_wechat(txt):
    def current_time():
        return (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).isoformat(sep=' ', timespec='seconds')
    
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
           "content" : current_time() + '\n' + txt
       }
    }
    
    r = requests.post(push_url, json = jsondata).json()
    print('push succeed!' if r['errcode'] == 0 else 'push failed! ' + r['errmsg'])

def invite(sid:str, s:requests.Session):
    invite_url = 'https://zt.wps.cn/2018/clock_in/api/invite'
    post_json = {'invite_userid': user_id,"client_code": client['code'], "client": client['type']}
    s.headers.update({'sid': sid})
    r = s.post(invite_url, json = post_json)
    #### debug
    print(r.text)
    ####
    short_sid = sid[:8] + '...' + sid[-6:]
    try:
        rjson = r.json()
        if rjson['result'] == 'ok':
            return {'ok':1, 'msg':'', 'sid':short_sid}
        elif rjson['result'] == 'error':
            return {'ok':0, 'msg':rjson['msg'], 'sid':short_sid}
    except json.JSONDecodeError:
        return {'ok':0, 'msg':'unknown error', 'sid':short_sid}

def get_result(my_sid:str):
    url = 'https://zt.wps.cn/2018/clock_in/api/get_data?member=wps'
    r = requests.get(url, headers={'sid':my_sid})
    res = {'ok':1}
    try:
        rjson = r.json()
        res['is_clock_in'] = rjson['is_clock_in']
        res['invite_count'] = int(rjson['invite_count'])
    except json.JSONDecodeError:
        res['ok':0]
    
    return res
   
def get_question(my_sid:str):
    url = 'https://zt.wps.cn/2018/clock_in/api/get_question?award=wps'
    r = requests.get(url, headers={'sid':my_sid})
    res = {'ok':1}
    try:
        rjson = r.json()
        if rjson['result'] == 'ok':
            res.update(rjson)
        else:
            res['ok'] = 0
    except json.JSONDecodeError:
        res['ok':0]
    return res
    
def answer_q(my_sid:str, ans:str):
    url = 'https://zt.wps.cn/2018/clock_in/api/answer?member=wps'
    post_json = {'answer': ans}
    r = requests.post(url, headers={'sid':my_sid}, json=post_json)
    res = {'ok':1, 'msg':''}
    try:
        rjson = r.json()
        if rjson['result'] != 'ok':
            res['ok'] = 0
            res['msg'] = rjson['msg']
    except json.JSONDecodeError:
        res['ok'] = 0
        res['msg'] = 'json decode error!'
    return res

def clock_in(my_sid:str):
    url = 'https://zt.wps.cn/2018/clock_in/api/clock_in?award=wps'
    stamp = int(time.time()*1000)
    param = '&client=%s&_t=%s&client_code=%s' % (client['type'], str(stamp), client['code'])
    url += param
    r = requests.get(url, headers={'sid':my_sid})
    res = {'ok':1, 'msg':''}
    try:
        rjson = r.json()
        if rjson['result'] != 'ok':
            res['ok'] = 0
            res['msg'] = rjson['msg']
    except json.JSONDecodeError:
        res['ok'] = 0
        res['msg'] = 'json decode error!'
    return res

def do_clock(my_sid:str):
    ans = '0'
    for cishu in range(10):
        question = get_question(my_sid)
        if question['ok']:
            for qa in qlist:
                if question['data']['title'] == qa['data']['title']:
                    ans = qa['data']['ans']
            if ans != '0':
                break
        else:
            print('Failed to get question.')
            push_wechat('Failed to get question.')
            break
        time.sleep(1)
    if ans == '0':
        print('no match ans')
        return {'ok':0}
    ret_ansq = answer_q(my_sid, ans)
    if ret_ansq['ok'] == 0:
        print('answer_q failed,', ret_ansq['msg'])
        return {'ok':0}
    ret_clock = clock_in(my_sid)
    if ret_clock['ok'] == 0:
        print('clock in failed,', ret_clock['msg'])
        return {'ok':0}
    print('clock in maybe succeed!')
    return {'ok':1}
        
# 主函数
def main():
    
    is_clock_in = -1
    invite_count = -1
    before_res = get_result(user_sid)
    if before_res['ok'] == 0:
        txt = 'get_result 函数出问题了！'
        print(txt)
        push_wechat(txt)
    else:
        is_clock_in = before_res['is_clock_in']
        invite_count = before_res['invite_count']
    if is_clock_in != 1:
        do_clock(user_sid)
    
    s = requests.session()
    err_txt = ''
    ok_count = 0
    fail_count = 0
    for one_sid in sid_list:
        res = invite(one_sid, s)
        if res['ok']:
            ok_count += 1
        else:
            fail_count += 1
            err_txt += res['sid'] + ', ' + res['msg'] + '\n'
        if one_sid is not sid_list[-1]:
            time.sleep(2.5) # 间隔2.5秒再邀请
    
    is_clock_in2 = -1
    invite_count2 = -1
    after_res = get_result(user_sid)
    if after_res['ok'] == 0:
        txt = 'get_result 函数出问题了！'
        print(txt)
        push_wechat(txt)
    else:
        invite_count2 = after_res['invite_count']
        is_clock_in2 = after_res['is_clock_in']
    
    
    clock_txt = ''
    if is_clock_in == 1:
        clock_txt = '今日已打卡，本次跳过'
    elif is_clock_in2 == 1:
        clock_txt = '本次打卡成功'
    else:
        clock_txt = '打卡失败，请查看报错信息'
    print(clock_txt)
    
    succ_count = -1
    if invite_count != -1 and after_res['ok']:
        succ_count = invite_count2 - invite_count
    
        
    push_txt = "WPS 通知推送"
    #push_txt += "\n尝试为【ID：%d】邀请 %d 位用户，其中：" % (user_id, count['total'])
    push_txt += '\n' + clock_txt
    push_txt += "\n本次邀请ok：%d，fail：%d，succ：%d" % (ok_count, fail_count, succ_count)
    push_txt += '\n今日累计邀请：%2d人' % invite_count2
    push_txt += '\n' + err_txt
        
    push_txt += '<a href="mp://F49Xy9rxwhOWm8o">会员打卡</a>'
    push_txt += '   <a href="mp://P2tulcSBYclooSc">稻壳签到</a>'
    push_txt += '   <a href="https://zt.wps.cn/spa/2019/vip_mobile_sign_v2/?from=wx_info_page&_wxv=20210302">积分签到</a>'
    push_wechat(push_txt)
        
def main_handler(event, context):
    return main()


def get_args():
    global user_id, client, user_sid, qlist
    
    for i in range(1,7):
        assert sys.argv[i] != "", "Lack of essential parameters!"
    user_id = sys.argv[1].strip()
    for item_sid in sys.argv[2].split(','):
        sid_list.append(item_sid)
    code_script = sys.argv[3]
    qywx_info.update(eval(sys.argv[4]))
    user_sid = sys.argv[5]
    qlist = eval(sys.argv[6]) 
    client = eval(code_script)
    assert type(client['code']) == str and len(client['code']) == 32, 'The code script you provided is wrong!'

def local_test():
    # do something test
    pass
if __name__ == '__main__':
    """
    for a in sys.argv:
        print("fuck:   ", a)
    """
    get_args()
    #local_test()
    main()
