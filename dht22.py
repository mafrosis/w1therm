#! /usr/bin/env python

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
logger.setLevel(logging.DEBUG)

# BCM pin numbering
GPIO_PIN_SSR = 23
GPIO_PIN_DHT22 = 24
GPIO_PIN_FAN = 17

TIME_SLEEP = 30


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
def resolve_jorg():
    logger.debug('Resolve jorg..')

    # discover jorg ip address via nslookup
    res = dns.resolver.Resolver()
    res.nameservers = ['192.168.1.1']

    #try:
    return [n for n in res.query('jorg.eggs')][0].address
    #except Exception as e:
    #    logger.error(e)


def send(jorg_addr, data):
    """
    Post sensor data to server
    """
    try:
        resp = requests.post('http://{}:8003/api/dht22/'.format(jorg_addr), json=data)

        if resp.status_code == 200:
            logger.info('Sent {} data points'.format(len(data)))

            # reset the data storage after a successful POST
            data = []
        else:
            logger.info('Server unavailable. Caching data point(s)')


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

    logger.debug('Humidity: {}'.format(hum))
    logger.debug('Temperature: {}'.format(temp))

    return hum, temp


def main():
    if not setup_gpio():
        logger.critical('Failed setting up GPIO')

    jorg_addr = resolve_jorg()

    data = []

    fridge_off = True

    while True:
        hum, temp = read()

        if fridge_off:
            if turn_fridge_on():
                fridge_off = False

            turn_fan_off()
        else:
            if turn_fridge_off():
                fridge_off = True

            turn_fan_on()

        # add data point to list
        data.append({
            'ts': str(datetime.datetime.now().timestamp()).split('.')[0],
            'temperature': temp,
            'humidity': hum,
        })

        #send(jorg_addr, data)
        time.sleep(TIME_SLEEP)
        logger.debug('TS: {}'.format(datetime.datetime.now()))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
