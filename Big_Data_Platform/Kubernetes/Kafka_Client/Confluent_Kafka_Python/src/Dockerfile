FROM python:3.7-slim as builder

RUN apt-get update \
&& apt-get install -y --no-install-recommends git-core curl build-essential gcc
WORKDIR /opt/
RUN curl https://codeload.github.com/edenhill/librdkafka/tar.gz/v1.6.0 | tar xzf -
WORKDIR /opt/librdkafka-1.6.0/
RUN ./configure --prefix=/usr \
&& make -j \
&& make install

WORKDIR /
COPY ./configurations/requirements.txt /
RUN pip3 install --user -r requirements.txt


from python:3.7-slim as app
COPY --from=builder /root/.local /root/.local
COPY --from=builder /usr/lib/librdkafka* /usr/lib/
ENV PATH=/root/.local/bin:$PATH