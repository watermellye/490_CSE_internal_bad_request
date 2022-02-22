from email import header
import requests
import os
import sys

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
import json
import time

js = {"README": "打开抓包软件；浏览器登录1.tongji；进去随便点些按钮，在headers中找到x-Token填入下方。", "token": "123456789abcdefg"}
if not os.path.exists("config.json"):
    with open("config.json", "w", encoding="utf-8") as fp:
        json.dump(js, fp, ensure_ascii=False)
    print("config.json已生成，请前去填写token")
    sys.exit(0)

with open("config.json", "r", encoding="utf-8") as fp:
    js = json.load(fp)


def save_js():
    with open("config.json", "w", encoding="utf-8") as fp:
        json.dump(js, fp, ensure_ascii=False)


def get(s, des="", **args):
    if des == "":
        des = s
    if s in js:
        return js[s]
    v = input(f"请输入{des}：\n").strip()
    try:
        if "str" not in args or args["str"] != 1:
            v = int(v)
    except:
        pass
    js[s] = v
    save_js()
    return v


headers = {
    'Host': '1.tongji.edu.cn',
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.56',
    'X-Token': get("token")
}


def get_id():
    if "id" in js:
        return int(js["id"])

    res = requests.post(url="https://1.tongji.edu.cn/api/electionservice/student/getRounds?projectId=1", headers=headers, timeout=100, verify=False)
    res = json.loads(res.text)
    print(res)
    res = res["data"]  # 如果在这里报错了，说明你token填错了。
    ids = []
    for i in res:
        print(f'\nid={i["id"]}\n{i["calendarName"]} {i["name"]}\n{i["beginTime"]} ~ {i["endTime"]}\n')
        ids.append(i["id"])

    if len(ids) != 1:
        ids = int(input("请从中选择本次选课id："))
    else:
        ids = ids[0]
    js["id"] = ids
    save_js()
    print(f"已为您自动记录选课id：{ids}")
    return ids


def get_course_info():
    res = requests.post(
        url=f'https://1.tongji.edu.cn/api/electionservice/student/getTeachClass4Limit?roundId={get_id()}&courseCode={get("course_id", "六位课号", str=1)}&studentId={get("student_id", "您的学号")}',
        headers=headers,
        timeout=100,
        verify=False)
    res = json.loads(res.text)
    res = res["data"]
    with open("course.json", "w", encoding="utf-8") as fp:
        json.dump(res, fp, ensure_ascii=False)
    elecClassList = {}
    print(res[0]["courseName"])
    for i in res:
        elecClassList[i["teachClassCode"]] = {"courseCode": i["courseCode"], "courseName": i["courseName"], "teachClassId": i["teachClassId"], "teachClassCode": i["teachClassCode"]}
        msg = []
        for j in i["timeTableList"]:
            msg.append(j["timeAndRoom"])
        print(f'{i["teachClassCode"][-2:]} : {i["teacherName"]} / {" ".join(msg)}')

    if len(elecClassList) != 1:
        elecClass = input("请从中选择想抢的课的课号：\n")
        elecClass = elecClassList[f'{get("course_id", str=1)}{elecClass}']

    else:
        elecClass = res[0]["teachClassCode"]
        print(f"已为您自动选择抢课课号：{elecClass}")
        elecClass = elecClassList[elecClass]
    js["elecClass"] = elecClass
    save_js()
    return elecClass


def qiangke():
    if "elecClass" not in js:
        get_course_info()
    data = {"roundId": get("id"), "elecClassList": [js["elecClass"]], "withdrawClassList": []}
    res = requests.post(url=f'https://1.tongji.edu.cn/api/electionservice/student/elect', headers=headers, data=json.dumps(data), timeout=100, verify=False)
    res = json.loads(res.text)
    while res["data"]["status"] == "Processing":
        res = requests.post(url=f'https://1.tongji.edu.cn/api/electionservice/student/5205/electRes', headers=headers, timeout=100, verify=False)
        res = json.loads(res.text)
        time.sleep(1)
    return res["data"]


first = True
while True:
    try:
        time.sleep(1)
        res = qiangke()
        # print(res)
        if res["failedReasons"] == {} and res["successCourses"] == []:
            if first:
                print("No Response: 您可能已选上该课程，或存在时间冲突。保险起见，本插件不会自动清退同时间段原课程，请先前往1.tongji解决冲突，随后重新填写数据。")
                js = {"README": "打开抓包软件；浏览器登录1.tongji；进去随便点些按钮，在headers中找到x-Token填入下方。", "token": js["token"]}
                save_js()
            else:
                print("Failed: No Response")
        if res["failedReasons"] != {}:
            print(f'Failed: {res["failedReasons"]}')
        if res["successCourses"] != []:
            print(f'Succeed: successCourses={res["successCourses"]}')
            break
        first = False
    except:
        print(f'Failed: 443')
