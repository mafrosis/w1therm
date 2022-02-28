ARG BASE_IMAGE=balenalib/raspberrypi3-python
FROM ${BASE_IMAGE}:3.9

ENV INITSYSTEM on
ENV TZ Australia/Melbourne
ENV CFLAGS -fcommon

WORKDIR /srv/app

COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY w1therm.py ./

CMD ["python3", "w1therm.py"]
