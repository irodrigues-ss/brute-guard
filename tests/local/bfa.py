import sys
import requests
import datetime

from concurrent.futures import ThreadPoolExecutor


def req():
    start = datetime.datetime.now()
    print(
        requests.post(
            "http://localhost:8001/login", json={"username": "teste", "password": "teste1"}
        ),
        start,
    )


def serial():
    for i in range(24):
        req()


def big_serial():
    for i in range(2000000):
        req()


def parallel():
    with ThreadPoolExecutor(8) as executor:
        for i in range(24):
            executor.submit(req)


args = sys.argv

if len(args) > 1 and args[1] == "-p":
    parallel()
else:
    serial()
