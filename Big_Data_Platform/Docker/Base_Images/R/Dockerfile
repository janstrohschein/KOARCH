FROM koarch/confluent_kafka_python:1.6.0

RUN apt-get update && apt-get install -y --no-install-recommends r-base r-base-dev build-essential libcurl4-gnutls-dev libxml2-dev libssl-dev

# python libs for r integration
RUN pip install rpy2
