import argparse
import json
import re
from datetime import datetime

import pytz
import requests
from bs4 import BeautifulSoup


class Report(object):
    def __init__(self, stuid, password, data_file):
        self.data_file = data_file
        self.session = self.login(stuid, password, "https://weixine.ustc.edu.cn/2020/caslogin")

    def login(self, stuid, password, service):
        print("Login...")

        data = {
            "model": "uplogin.jsp",
            "service": service,
            "warn": "",
            "showCode": "",
            "username": stuid,
            "password": password,
            "button": "",
        }
        session = requests.Session()
        session.post("https://passport.ustc.edu.cn/login", data=data)

        print("Login Successfully!")

        return session

    def report(self):
        html = self.session.get("https://weixine.ustc.edu.cn/2020").text
        soup = BeautifulSoup(html, "html.parser")
        token = soup.find("input", {"name": "_token"})["value"]

        with open(self.data_file, "r+") as f:
            data = f.read()
            data = json.loads(data)
            data["_token"] = token

        self.session.post("https://weixine.ustc.edu.cn/2020/daliy_report", data=data)

        return self.check()

    def check(self):
        html = self.session.get("https://weixine.ustc.edu.cn/2020").text
        soup = BeautifulSoup(html, "html.parser")
        date_text = soup.find("span", {"style": "position: relative; top: 5px; color: #666;"}).text
        pattern = re.compile("202[0-9]-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}")

        if date := pattern.search(date_text).group():
            print("Latest Report:", date)
            date += " +0800"
            report_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S %z")
            now_time = datetime.now(pytz.timezone("Asia/Shanghai"))
            delta = now_time - report_time
            if delta.seconds < 60:
                return True

        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="URC ncov AutoReport")
    parser.add_argument("data_file", help="Path to your own data", type=str)
    parser.add_argument("stuid", help="Student ID", type=str)
    parser.add_argument("password", help="Password", type=str)
    args = parser.parse_args()

    auto_reporter = Report(stuid=args.stuid, password=args.password, data_file=args.data_file)

    for i in range(3):
        try:
            if auto_reporter.report():
                print("Report Successfully!")
                break
        except:
            pass
        print("Report Failed. Retry...")
    else:
        print("Report Failed!")
        exit(-1)
