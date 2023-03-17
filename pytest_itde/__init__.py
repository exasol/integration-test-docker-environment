import os
from typing import Tuple

import pyexasol
import pytest

from pytest_itde import config

EXASOL = config.OptionGroup(
    prefix="exasol",
    options=(
        {
            "name": "host",
            "type": str,
            "default": "localhost",
            "help_text": "Host to connect to",
        },
        {
            "name": "port",
            "type": int,
            "default": 8888,
            "help_text": "Port on which the exasol db is listening",
        },
        {
            "name": "username",
            "type": str,
            "default": "SYS",
            "help_text": "Username used to authenticate against the exasol db",
        },
        {
            "name": "password",
            "type": str,
            "default": "exasol",
            "help_text": "Password used to authenticate against the exasol db",
        },
    ),
)

BUCKETFS = config.OptionGroup(
    prefix="bucketfs",
    options=(
        {
            "name": "url",
            "type": str,
            "default": "http://127.0.0.1:6666",
            "help_text": "Base url used to connect to the bucketfs service",
        },
        {
            "name": "username",
            "type": str,
            "default": "w",
            "help_text": "Username used to authenticate against the bucketfs service",
        },
        {
            "name": "password",
            "type": str,
            "default": "write",
            "help_text": "Password used to authenticate against the bucketfs service",
        },
    ),
)


def TestSchemas(value) -> Tuple[str]:
    seperator = ","
    if seperator in value:
        schemas = value.split(seperator)
    else:
        schemas = [value]
    schemas = (s.strip() for s in schemas)
    schemas = (s for s in schemas if s != "")
    return tuple(schemas)


ITDE = config.OptionGroup(
    prefix="itde",
    options=(
        {
            "name": "db_version",
            "type": str,
            "default": "7.1.17",
            "help_text": "DB version to start, if value is 'external' an existing instance will be used",
        },
        {
            "name": "schemas",
            "type": TestSchemas,
            "default": ("TEST", "TEST_SCHEMA"),
            "help_text": "Schemas which should be created for the session",
        },
    ),
)


@pytest.fixture(scope="session")
def exasol_config(request) -> config.Exasol:
    cli_arguments = request.config.option
    kwargs = EXASOL.kwargs(os.environ, cli_arguments)
    return config.Exasol(**kwargs)


@pytest.fixture(scope="session")
def bucketfs_config(request) -> config.BucketFs:
    cli_arguments = request.config.option
    kwargs = BUCKETFS.kwargs(os.environ, cli_arguments)
    return config.BucketFs(**kwargs)


@pytest.fixture(scope="session")
def itde_config(request) -> config.Itde:
    cli_arguments = request.config.option
    kwargs = ITDE.kwargs(os.environ, cli_arguments)
    return config.Itde(**kwargs)


@pytest.fixture(scope="session")
def connection_factory():
    connections = []

    def factory(config: config.Exasol):
        con = pyexasol.connect(
            dsn=f"{config.host}:{config.port}",
            user=config.username,
            password=config.password,
        )
        connections.append(con)
        return con

    yield factory

    for connection in connections:
        connection.close()


@pytest.fixture(scope="session")
def bootstrap_db(itde_config, exasol_config, bucketfs_config):
    def nop():
        pass

    def start_db(name, itde, exasol, bucketfs):
        import exasol_integration_test_docker_environment.lib.api.spawn_test_environment as api
        from urllib.parse import urlparse
        bucketfs_url = urlparse(bucketfs.url)
        _, cleanup_function = api.spawn_test_environment(
            environment_name=name,
            database_port_forward=exasol.port,
            bucketfs_port_forward=bucketfs_url.port,
            db_mem_size="4GB",
            docker_db_image_version=itde.db_version,
        )
        return cleanup_function

    db_name = "pytest_exasol_db"
    bootstrap_db = itde_config.db_version != "external"

    start = (
        lambda: start_db(db_name, itde_config, exasol_config, bucketfs_config)
        if bootstrap_db
        else lambda: nop
    )
    stop = start()
    yield
    stop()


@pytest.fixture(scope="session")
def itde(
        bootstrap_db,
        itde_config,
        exasol_config,
        bucketfs_config,
        connection_factory,
) -> config.TestConfig:
    connection = connection_factory(exasol_config)

    for schema in itde_config.schemas:
        connection.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
        connection.execute(f"CREATE SCHEMA {schema};")
        connection.commit()

    yield config.TestConfig(
        db=exasol_config,
        bucketfs=bucketfs_config,
        itde=itde_config,
        ctrl_connection=connection,
    )

    for schema in itde_config.schemas:
        connection.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
        connection.commit()


OPTION_GROUPS = (EXASOL, BUCKETFS, ITDE)


def _add_option_group(parser, group):
    parser_group = parser.getgroup(group.prefix)
    for option in group.options:
        parser_group.addoption(
            option.cli,
            type=option.type,
            help=option.help,
        )


def pytest_addoption(parser):
    for group in OPTION_GROUPS:
        _add_option_group(parser, group)
