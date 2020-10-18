FROM balenalib/raspberry-pi2-python:3.7.4

ENV INITSYSTEM on
ENV TZ Australia/Melbourne

RUN apt-get update && apt-get install -y build-essential

WORKDIR /srv/app

ADD ./Adafruit_Python_DHT Adafruit_Python_DHT
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY fridge.py ./

CMD ["python", "fridge.py"]
