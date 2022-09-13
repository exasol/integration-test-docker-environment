FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive


RUN apt-get -y update && \
    apt-get -y install \
        locales \
        curl && \
    locale-gen en_US.UTF-8 && \
    update-locale LC_ALL=en_US.UTF-8 && \
    apt-get -y clean && \
    apt-get -y autoremove && \
    ldconfig

RUN mkdir -p /scripts
COPY create_certificates.sh /scripts/create_certificates.sh
