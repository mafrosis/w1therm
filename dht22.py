#! /usr/bin/env python

import datetime
import time

import Adafruit_DHT
import dns.resolver
import requests


def init():
    while True:
        # discover jorg ip address via nslookup
        res = dns.resolver.Resolver()
        res.nameservers = ['192.168.1.1']

        try:
            return [n for n in res.query('jorg.eggs')][0].address
        except Exception as e:
            print(e)
            time.sleep(60)


def main():
    jorg_addr = init()

    while True:
        hum, temp = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 25)

        print('{:.1f}, {:.1f}'.format(hum, temp))

        payload = {
            'ts': datetime.datetime.now().isoformat().split('.')[0],
            'temperature': temp,
            'humidity': hum,
        }
        requests.post('http://{}:8003/api/dht22/'.format(jorg_addr), json=payload)
        time.sleep(60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
