#! /usr/bin/env python3

import datetime
import logging
import os
import time

import Adafruit_DHT
import paho.mqtt.publish as publish
import RPi.GPIO as GPIO


# setup logging
logger = logging.getLogger(__name__)
sh = logging.StreamHandler()
logger.addHandler(sh)
logger.setLevel(logging.INFO)

if os.environ.get('DEBUG'):
    logger.setLevel(logging.DEBUG)


# BCM pin numbering  https://pinout.xyz
GPIO_PIN_DHT22 = 18

TIME_SLEEP = 60
MQTT_HOST = 'ringil'
MQTT_TOPIC_ROOM = 'servercloset'


def main():
    logger.info('dht22_2')
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    try:
        while True:
            try:
                humidity, temp = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, GPIO_PIN_DHT22)
                if temp is None or humidity is None:
                    raise RuntimeError

                logger.debug('%s %s %s', datetime.datetime.now(), f'{temp:.1f}', f'{humidity:.1f}')

            except RuntimeError as e:
                if e:
                    logger.error(e)
                # if the sensor fails, retry immediately
                time.sleep(0.2)
                continue

            msgs = [
                (f'home/{MQTT_TOPIC_ROOM}/temperature', temp),
                (f'home/{MQTT_TOPIC_ROOM}/humidity', humidity),
            ]
            ret = publish.multiple(msgs, hostname=MQTT_HOST)

            time.sleep(TIME_SLEEP-1)
    finally:
        logger.info('fin')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
