#! /usr/bin/env python3

import datetime
import json
import logging
import os
import sys
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
GPIO_PIN_DHT22 = os.environ.get('GPIO_PIN_DHT22')
if not GPIO_PIN_DHT22:
    GPIO_PIN_DHT22 = 18
    logger.info('GPIO_PIN_DHT22 has been defaulted to 18')
else:
    logger.info('GPIO_PIN_DHT22 has been set to %s', GPIO_PIN_DHT22)

TIME_SLEEP = 60


def main():
    MQTT_HOST = os.environ.get('MQTT_HOST')
    MQTT_TOPIC_ROOM = os.environ.get('MQTT_TOPIC_ROOM')
    HA_SENSOR_NAME = os.environ.get('HA_SENSOR_NAME')

    if not MQTT_HOST:
        logger.info('You must set MQTT_HOST environment var')
        sys.exit(1)
    if not MQTT_TOPIC_ROOM:
        if HA_SENSOR_NAME:
            MQTT_TOPIC_ROOM = HA_SENSOR_NAME.replace(' ', '_').lower()
            logger.info('MQTT_TOPIC_ROOM has been set to "%s" based on HA_SENSOR_NAME', HA_SENSOR_NAME)
        else:
            logger.info('You must set MQTT_TOPIC_ROOM environment var')
            sys.exit(1)

    if os.environ.get('HA_SENSOR_NAME'):
        autoconfigure_ha_sensors(MQTT_HOST, MQTT_TOPIC_ROOM)

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


def autoconfigure_ha_sensors(mqtt_host, mqtt_topic):
    '''Send discovery messages to auto configure the sensors in HA'''

    # Set a device name for these sensors in HA
    HA_DEVICE = os.environ.get('HA_DEVICE')

    # Set a friendly name that the sensor will display in HA UI
    HA_SENSOR_NAME = os.environ.get('HA_SENSOR_NAME')

    if not HA_DEVICE:
        logger.info('You must set HA_DEVICE environment var')
        sys.exit(1)
    if not HA_SENSOR_NAME:
        logger.info('You must set HA_SENSOR_NAME environment var')
        sys.exit(1)

    # Configure both temperature and humidity
    for sensor, unit in (('temperature', '°C'), ('humidity', '%')):
        publish.single(
            f'homeassistant/sensor/{HA_DEVICE}_dht22/{sensor}/config',
            json.dumps({
                'name': '{} {}'.format(HA_SENSOR_NAME, sensor.title()),
                'unique_id': f'{mqtt_topic}_{sensor}',
                'device_class': sensor,
                'state_topic': f'home/{mqtt_topic}/{sensor}',
                'unit_of_measurement': unit,
                'device': {
                    'identifiers': [HA_DEVICE, 'raspberrypi'],
                    'name': f'{HA_DEVICE} DHT22',
                    'model': 'DHT22',
                }
            }),
            hostname=mqtt_host,
        )

    logger.info('Autodiscovery topic published for "%s_%s" on device "%s DHT22"', mqtt_topic, sensor, HA_DEVICE)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
