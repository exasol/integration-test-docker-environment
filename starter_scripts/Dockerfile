FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive

COPY ext/01_nodoc /etc/dpkg/dpkg.cfg.d/01_nodoc

RUN apt-get -y update && \
    apt-get -y install --no-install-recommends\
        ca-certificates \
        locales \
        python3.8-venv \
        git \
        bash \
        curl && \
    locale-gen en_US.UTF-8 && \
    update-locale LC_ALL=en_US.UTF-8 && \
    apt-get -y clean && \
    apt-get -y autoremove && \
    ldconfig

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN mkdir /exasol_integration_test_docker_environment
COPY exasol_integration_test_docker_environment /integration_test_docker_environment/exasol_integration_test_docker_environment
COPY pytest_itde /integration_test_docker_environment/pytest_itde
COPY poetry.lock /integration_test_docker_environment/poetry.lock
COPY pyproject.toml /integration_test_docker_environment/pyproject.toml
COPY LICENSE /integration_test_docker_environment/LICENSE
COPY README.rst /integration_test_docker_environment/README.rst

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH /root/.local/bin:$PATH
RUN poetry config virtualenvs.create false

WORKDIR /integration_test_docker_environment
RUN poetry install

COPY starter_scripts /integration_test_docker_environment/starter_scripts
