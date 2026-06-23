import psutil
import requests
import time

SERVER_URL = "http://localhost:8000/events/"
WHITE_LIST = ["chrome.exe", "code.exe", "python.exe"]

def monitoring():
    while True:
        for processes in psutil.process_iter(['pid', 'name']):
            name = processes.info['name']
            if name in WHITE_LIST:
                event = {
                    "proceso": name,
                    "pid": processes.info['pid'],
                }
                requests.post(SERVER_URL, json=event)
        time.sleep(5)
if __name__ == "__main__":
    monitoring()
