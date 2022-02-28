#! /usr/bin/env python3

import datetime
import json
import logging
import os
import sys
import time

import paho.mqtt.publish as publish
from w1thermsensor import W1ThermSensor
from w1thermsensor.errors import W1ThermSensorError


# setup logging
logger = logging.getLogger(__name__)
sh = logging.StreamHandler()
logger.addHandler(sh)
logger.setLevel(logging.INFO)

if os.environ.get('DEBUG'):
    logger.setLevel(logging.DEBUG)


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
            logger.info('You must set MQTT_TOPIC_ROOM or HA_SENSOR_NAME environment var')
            sys.exit(1)

    if os.environ.get('HA_SENSOR_NAME'):
        autoconfigure_ha_sensors(MQTT_HOST, MQTT_TOPIC_ROOM)


    try:
        while True:
            for sensor in W1ThermSensor.get_available_sensors():
                try:
                    temp = sensor.get_temperature()

                    logger.debug('%s %s', datetime.datetime.now(), f'{temp:.1f}')

                except W1ThermSensorError as e:
                    if e:
                        logger.error(e)
                    # if the sensor fails, retry in a couple of seconds
                    time.sleep(2)
                    continue

            msgs = [
                (f'home/{MQTT_TOPIC_ROOM}/temperature', temp),
            ]
            publish.multiple(msgs, hostname=MQTT_HOST)

            time.sleep(TIME_SLEEP-1)
    finally:
        logger.info('fin')


def autoconfigure_ha_sensors(mqtt_host, mqtt_topic):
    '''Send discovery messages to auto configure the sensors in HA'''

    # Required in Home Assistant to group the sensors against a device
    HA_DEVICE = os.environ.get('HA_DEVICE')

    # The friendly name shown in the Home Assistant UI
    HA_SENSOR_NAME = os.environ.get('HA_SENSOR_NAME')

    if not HA_DEVICE:
        logger.info('You must set HA_DEVICE environment var')
        sys.exit(1)
    if not HA_SENSOR_NAME:
        logger.info('You must set HA_SENSOR_NAME environment var')
        sys.exit(1)

    # Configure both temperature
    for sensor, unit in (('temperature', '°C'),):
        publish.single(
            f'homeassistant/sensor/{HA_DEVICE}_w1therm/{sensor}/config',
            json.dumps({
                'name': '{} {}'.format(HA_SENSOR_NAME, sensor.title()),
                'unique_id': f'{mqtt_topic}_{sensor}',
                'device_class': sensor,
                'state_topic': f'home/{mqtt_topic}/{sensor}',
                'unit_of_measurement': unit,
                'device': {
                    'identifiers': [HA_DEVICE, 'raspberrypi'],
                    'name': f'{HA_DEVICE} w1therm',
                    'model': 'DS18B20',
                }
            }),
            hostname=mqtt_host,
            retain=True,
        )

        logger.info('Autodiscovery topic published for "%s_%s" on device "%s w1therm"',
                    mqtt_topic, sensor, HA_DEVICE)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
