import configparser
import os
conf = configparser.ConfigParser()
# 读ini文件
conf.read(os.path.join(os.getcwd(), "config.ini"), encoding="utf-8")

if __name__ == '__main__':
    print(conf.get("app", "home"))