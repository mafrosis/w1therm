DHT22 for Rpi and Home Assistant
================================

A simple python app running in docker for reading a DHT22 and sending via MQTT. Autodiscovery for
Home Assistant is baked in.


Building
--------

The default base image is `balenalib/raspberrypi3-python`, which is suitable for raspberrypi3/4:

    docker-compose build

Or, [specify a different base image](https://www.balena.io/docs/reference/base-images/base-images-ref),
for example a raspberrypi zero:

    docker-compose build --build-arg BASE_IMAGE=balenalib/raspberry-pi-python


Running
-------

You are required to specify at least two environment variables. Export these in your shell before
running the `docker-compose up` command.

In the simplest configuration, an MQTT broker and an MQTT topic are required:

 * `MQTT_HOST=<hostname or IP>`
 * `MQTT_TOPIC_ROOM=kitchen`


And in Home Assistant autodiscovery mode:

 * `MQTT_HOST=<hostname or IP>`
 * `HA_DEVICE=rpi4`
 * `HA_SENSOR_NAME='Living Room'`

`HA DEVICE` is required in Home Assistant to group the sensors against a device.

`HA_SENSOR_NAME` is the friendly name shown in the Home Assistant UI.

NOTE: in this configuration the MQTT topic is derived from the `HA_SENSOR_NAME` setting.


And to start the app:

    docker-compose up


MQTT Topic
----------

The temperature/humidity messages are published on:

 * `home/<MQTT_TOPIC_ROOM>/temperature`
 * `home/<MQTT_TOPIC_ROOM>/humidity`
