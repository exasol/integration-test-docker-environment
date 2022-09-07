FROM ubuntu:20.04

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
RUN curl -s https://www.exasol.com/support/secure/attachment/175394/EXAplus-7.1.3.tar.gz | tar -C downloads/EXAplus --strip-components 1 -zxf -
ENV EXAPLUS=/downloads/EXAplus/exaplus