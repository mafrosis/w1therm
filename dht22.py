#! /usr/bin/env python3

import datetime
import logging
import time

import Adafruit_DHT
import dns.resolver
import requests

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    # dummy GPIO for unit testing (this is mocked)
    import time as GPIO


# setup logging
logger = logging.getLogger(__name__)
sh = logging.StreamHandler()
logger.addHandler(sh)
logger.setLevel(logging.INFO)

# BCM pin numbering
GPIO_PIN_SSR = 23
GPIO_PIN_DHT22 = 24
GPIO_PIN_FAN = 17

TIME_SLEEP = 10

TARGET_TEMP = 7.0

HASSIO_AUTH_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiIzOTIwODFiMzdhZGY0ZmFhODg1ZjNlNTkyYWQ0MGM3MCIsImlhdCI6MTU2MDI1MzIxNiwiZXhwIjoxODc1NjEzMjE2fQ.HHDEeRRlJXKWhb0l_UYuWzkBA4DoUqpTczt70V_CLIw"


def retry_forever(f):
    def wrapped(*args, **kwargs):
        retry = 1
        success = False

        while not success:
            try:
                res = f(*args, **kwargs)
                success = True
            except Exception:
                # exponential sleep, capped at 64 secs
                sleep = retry**2
                if sleep > 64:
                    sleep = 64

                logger.debug('Sleeping {}.. (retry {})'.format(sleep, retry))
                time.sleep(sleep)
                retry += 1

        logger.debug('Completed {}'.format(f.__name__))
        return res

    return wrapped


@retry_forever
def setup_gpio():
    logger.debug('Setup GPIO..')

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(GPIO_PIN_SSR, GPIO.OUT)
    GPIO.setup(GPIO_PIN_FAN, GPIO.OUT)

    # ensure fridge off at start up
    turn_fridge_off()
    turn_fan_off()

    return True


def turn_fridge_off():
    logger.debug('Fridge switched off (pin low)')
    GPIO.output(GPIO_PIN_SSR, GPIO.LOW)
    return True


def turn_fridge_on():
    logger.debug('Fridge switched on (pin high)')
    GPIO.output(GPIO_PIN_SSR, GPIO.HIGH)
    return True


def turn_fan_off():
    logger.debug('Fan switched off (pin low)')
    GPIO.output(GPIO_PIN_FAN, GPIO.LOW)
    return True


def turn_fan_on():
    logger.debug('Fan switched on (pin high)')
    GPIO.output(GPIO_PIN_FAN, GPIO.HIGH)
    return True


@retry_forever
def resolve_homeassistant():
    logger.debug('Resolve homeassistant on ringil..')

    # discover ringil ip address via nslookup
    res = dns.resolver.Resolver()
    res.nameservers = ['192.168.1.1']

    try:
        return [n for n in res.query('ringil.eggs')][0].address
    except Exception as e:
        logger.warning(e)


def send(homeassistant_addr, name, state, binary=False, attrs=None):
    """
    Post sensor data to server
    """
    data = {'state': state}

    if attrs:
        data['attributes'] = attrs

    try:
        resp = requests.post(
            'http://{}:8123/api/states/{}sensor.fridge_{}'.format(
                homeassistant_addr, 'binary_' if binary is True else '', name
            ),
            json=data,
            headers={'Authorization': 'Bearer {}'.format(HASSIO_AUTH_TOKEN)},
        )

        if resp.status_code in (200, 201):
            logger.debug('{} returned logging to hass.io: {}'.format(resp.status_code, data))

            # reset the data storage after a successful POST
            data = []
        else:
            logger.error(resp.text)

    except requests.exceptions.RequestException:
        # payload has been stored for POST next time
        pass


def read():
    """
    Read the DHT22 data pin for temperature and humidity
    """
    hum, temp = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, GPIO_PIN_DHT22)

    if temp is None or hum is None:
        if hum is None:
            logger.critical('Humidity reporting null')

        if temp is None:
            logger.critical('Temp reporting null')

        return hum or 0, temp or 0

    logger.info('Humidity: {}'.format(hum))
    logger.info('Temperature: {}'.format(temp))

    return hum, temp


def main():
    if not setup_gpio():
        logger.critical('Failed setting up GPIO')

    # discover hass.io via DNS
    hassio_addr = resolve_homeassistant()
    logger.info('Hass.io found at {}'.format(hassio_addr))
    logger.info('Target temperature is {}'.format(TARGET_TEMP))

    fridge_off = True
    fan_off = True

    while True:
        hum, temp = read()

        if datetime.datetime.now().minute % 10 == 0:
            logger.info('Target temperature is {}'.format(TARGET_TEMP))

        if temp > TARGET_TEMP:
            if turn_fridge_on():
                fridge_off = False
        else:
            if turn_fridge_off():
                fridge_off = True

        fridge_power_state = 'on' if not fridge_off else 'off'
        logger.info('Fridge is {}'.format(fridge_power_state))

        # run the fan every other minute
        if datetime.datetime.now().minute % 2 == 0:
            if turn_fan_on():
                fan_off = False
        else:
            if turn_fan_off():
                fan_off = True

        fan_power_state = 'on' if not fan_off else 'off'
        logger.info('Fan is {}'.format(fan_power_state))

        # log historic data
        if hassio_addr:
            send(hassio_addr, 'temperature', '{:.1f}'.format(temp))
            send(hassio_addr, 'humidity', '{:.1f}'.format(hum))
            send(hassio_addr, 'power', fridge_power_state, binary=True)
            send(hassio_addr, 'fan_power', fan_power_state, binary=True)

        time.sleep(TIME_SLEEP)
        logger.debug('TS: {}'.format(datetime.datetime.now()))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
