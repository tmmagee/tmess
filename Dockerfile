# VERSION 0.0.0
# DOCKER-VERSION 0.8.0

FROM stackbrew/ubuntu:precise
MAINTAINER Gabriel Farrell gsf747@gmail.com

RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y gunicorn python-dateutil python-feedparser python-psycopg2 wget ca-certificates

# Install Django
RUN wget -nv https://www.djangoproject.com/m/releases/1.4/Django-1.4.10.tar.gz
RUN tar xzf Django-1.4.10.tar.gz
RUN cd Django-1.4.10 && python setup.py -q install
RUN rm -rf Django-1.4.10*

ADD docker/etc /etc

# Override this with volume mount for local development
ADD mess /usr/local/src/mess

WORKDIR /usr/local/src

ENTRYPOINT ["gunicorn", "mess.wsgi:application", "-b0.0.0.0:8000", "--max-workers", "1"]

EXPOSE 8000
