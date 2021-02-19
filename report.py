import argparse
import json
import re
from datetime import datetime

import pytz
import requests
from bs4 import BeautifulSoup


class Report(object):
    def __init__(self, stuid, password, data_file):
        self.stuid = stuid
        self.password = password
        self.data_file = data_file

    def report(self):
        session = self.login()
        cookies = session.cookies

        data = session.get("https://weixine.ustc.edu.cn/2020").text
        data = data.encode("ascii", "ignore").decode("utf-8", "ignore")
        soup = BeautifulSoup(data, "html.parser")
        token = soup.find("input", {"name": "_token"})["value"]

        with open(self.data_file, "r+") as f:
            data = f.read()
            data = json.loads(data)
            data["_token"] = token

        cookies = "laravel_session=" + cookies.get("laravel_session")

        headers = {"cookie": cookies}

        url = "https://weixine.ustc.edu.cn/2020/daliy_report"
        session.post(url, data=data, headers=headers)
        data = session.get("https://weixine.ustc.edu.cn/2020").text
        soup = BeautifulSoup(data, "html.parser")
        token = soup.find("span", {"style": "position: relative; top: 5px; color: #666;"}).text
        pattern = re.compile("202[0-9]-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}")

        flag = False
        if date := pattern.search(token).group():
            print("Latest report:", date)
            date += " +0800"
            report_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S %z")
            now_time = datetime.now(pytz.timezone("Asia/Shanghai"))
            delta = now_time - report_time
            print(delta.seconds)
            if delta.seconds < 60:
                flag = True

        if flag:
            print("Report SUCCESSFUL!")
        else:
            print("Report FAILED!")

        return flag

    def login(self):
        print("Login...")

        url = "https://passport.ustc.edu.cn/login"
        data = {
            "model": "uplogin.jsp",
            "service": "https://weixine.ustc.edu.cn/2020/caslogin",
            "warn": "",
            "showCode": "",
            "username": self.stuid,
            "password": self.password,
            "button": "",
        }
        session = requests.Session()
        session.post(url, data=data)

        return session


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="URC ncov AutoReport")
    parser.add_argument("data_file", help="Path to your own data", type=str)
    parser.add_argument("stuid", help="Student ID", type=str)
    parser.add_argument("password", help="Password", type=str)
    args = parser.parse_args()
    auto_reporter = Report(stuid=args.stuid, password=args.password, data_file=args.data_file)

    for i in range(3):
        if auto_reporter.report():
            break
        print("Report Failed, retry...")
    else:
        exit(-1)
