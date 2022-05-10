FROM ubuntu:18.04

COPY ext/01_nodoc /etc/dpkg/dpkg.cfg.d/01_nodoc

RUN apt-get -y update && \
    apt-get -y install \
        openjdk-11-jdk \
        perl \
        locales \
        curl && \
    locale-gen en_US.UTF-8 && \
    update-locale LC_ALL=en_US.UTF-8 && \
    apt-get -y clean && \
    apt-get -y autoremove && \
    ldconfig

RUN curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh

RUN mkdir -p downloads/JDBC downloads/EXAplus
RUN curl -s https://www.exasol.com/support/secure/attachment/175412/EXASOL_JDBC-7.1.3.tar.gz | tar -C downloads/JDBC --strip-components 1 -zxf -
RUN curl -s https://www.exasol.com/support/secure/attachment/175394/EXAplus-7.1.3.tar.gz | tar -C downloads/EXAplus --strip-components 1 -zxf -
ENV EXAPLUS=/downloads/EXAplus/exaplus
