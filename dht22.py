#! /usr/bin/env python

import datetime
import time

import Adafruit_DHT
import requests


def main():
    while True:
        hum, temp = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 25)

        print('{:.1f}, {:.1f}'.format(hum, temp))

        payload = {
            'ts': datetime.datetime.now().isoformat().split('.')[0],
            'temperature': temp,
            'humidity': hum,
        }
        requests.post('http://jorg.eggs:8003/api/dht22/', data=payload)
        time.sleep(60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
