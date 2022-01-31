FROM ubuntu:18.04

COPY ext/01_nodoc /etc/dpkg/dpkg.cfg.d/01_nodoc

RUN apt-get -y update && \
    apt-get -y install --no-install-recommends\
        ca-certificates \
        locales \
        python3-wheel \
        python3-setuptools \
        git \
        bash \
        curl && \
    locale-gen en_US.UTF-8 && \
    update-locale LC_ALL=en_US.UTF-8 && \
    apt-get -y clean && \
    apt-get -y autoremove && \
    ldconfig

RUN curl https://bootstrap.pypa.io/pip/3.6/get-pip.py | python3

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN mkdir /exasol_integration_test_docker_environment
COPY exasol_integration_test_docker_environment /integration_test_docker_environment/exasol_integration_test_docker_environment
COPY poetry.lock /integration_test_docker_environment/poetry.lock
COPY pyproject.toml /integration_test_docker_environment/pyproject.toml
COPY setup.py /integration_test_docker_environment/setup.py
COPY LICENSE /integration_test_docker_environment/LICENSE
COPY README.md /integration_test_docker_environment/README.md

WORKDIR /integration_test_docker_environment
RUN python3 -m pip install .

COPY starter_scripts /integration_test_docker_environment/starter_scripts
