FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -y update && \
    apt-get -y install \
        perl \
        openjdk-11-jdk \
        locales \
        curl && \
    locale-gen en_US.UTF-8 && \
    update-locale LC_ALL=en_US.UTF-8 && \
    apt-get -y clean && \
    apt-get -y autoremove && \
    ldconfig


RUN curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh

RUN mkdir -p downloads/EXAplus
RUN curl -s https://x-up.s3.amazonaws.com/7.x/7.1.16/EXAplus-7.1.16.tar.gz | tar -C downloads/EXAplus --strip-components 1 -zxf -
ENV EXAPLUS=/downloads/EXAplus/exaplus

COPY test.text /test.text