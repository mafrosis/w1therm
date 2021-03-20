ARG BASE_IMAGE=balenalib/raspberrypi3-python
FROM ${BASE_IMAGE}:3.8

ENV INITSYSTEM on
ENV TZ Australia/Melbourne

RUN apt-get update && apt-get install -y build-essential
RUN pip install --upgrade wheel setuptools

WORKDIR /srv/app

ADD ./Adafruit_Python_DHT Adafruit_Python_DHT
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY dht22.py ./

CMD ["python3", "dht22.py"]
