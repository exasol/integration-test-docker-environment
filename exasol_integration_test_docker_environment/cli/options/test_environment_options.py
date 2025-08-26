import click

from exasol_integration_test_docker_environment.lib.test_environment.parameter.docker_db_test_environment_parameter import (
    DbOsAccess,
)
from exasol_integration_test_docker_environment.lib.test_environment.ports import Ports

test_environment_options = [
    click.option(
        "--environment-type",
        type=click.Choice(["docker_db", "external_db"]),
        default="""docker_db""",
        show_default=True,
        help="""Environment type for tests.""",
    ),
    click.option(
        "--max_start_attempts",
        type=int,
        default=2,
        show_default=True,
        help="""Maximum start attempts for environment""",
    ),
]

LATEST_DB_VERSION = """2025.1.0"""
DEFAULT_MEM_SIZE = """2 GiB"""
DEFAULT_DISK_SIZE = """2 GiB"""

docker_db_options = [
    click.option(
        "--docker-db-image-version",
        type=str,
        default=LATEST_DB_VERSION,
        show_default=True,
        help="""Docker DB Image Version against which the tests should run.""",
    ),
    click.option(
        "--docker-db-image-name",
        type=str,
        default="""exasol/docker-db""",
        show_default=True,
        help="""Docker DB Image Name against which the tests should run.""",
    ),
    click.option(
        "--db-os-access",
        type=click.Choice([e.name for e in DbOsAccess]),
        metavar="METHOD",
        default="""DOCKER_EXEC""",
        show_default=True,
        help="""How to access file system and command line of the
     		 database operating system. Experimental option, will show no
     		 effect until implementation of feature SSH access is
     		 completed.""",
    ),
    click.option(
        "--create-certificates/--no-create-certificates",
        default=False,
        help="""Creates and injects SSL certificates to the Docker DB container.""",
    ),
    click.option(
        "--additional-db-parameter",
        "-p",
        type=str,
        multiple=True,
        help="""Additional database parameter which will be injected to EXAConf. Value should have format '-param=value'.""",
    ),
    click.option(
        "--docker-environment-variable",
        type=str,
        multiple=True,
        default=[],
        help="""An environment variable which will be added to the docker-db.
                The variable needs to have format "key=value".
                For example "HTTPS_PROXY=192.168.1.5".
                You can repeat this option to add further environment variables.""",
    ),
]

external_db_options = [
    click.option(
        "--external-exasol-db-host",
        type=str,
        help="""Host name or IP of external Exasol DB, needs to be set if --environment-type=external_db""",
    ),
    click.option(
        "--external-exasol-db-port",
        type=int,
        default=Ports.external.database,
        help="""Database port of external Exasol DB, needs to be set if --environment-type=external_db""",
    ),
    click.option(
        "--external-exasol-bucketfs-port",
        type=int,
        default=Ports.external.bucketfs,
        help="""Bucketfs port of external Exasol DB, needs to be set if --environment-type=external_db""",
    ),
    click.option(
        "--external-exasol-ssh-port",
        type=int,
        help="""SSH port of external Exasol DB, needs to be set if --environment-type=external_db""",
    ),
    click.option(
        "--external-exasol-db-user",
        type=str,
        help="""User for external Exasol DB, needs to be set if --environment-type=external_db""",
    ),
    click.option(
        "--external-exasol-db-password",
        type=str,
        help="""Database Password for external Exasol DB""",
    ),
    click.option(
        "--external-exasol-bucketfs-write-password",
        type=str,
        help="""BucketFS write Password for external Exasol DB""",
    ),
    click.option(
        "--external-exasol-xmlrpc-host",
        type=str,
        help="""Hostname for the xmlrpc server""",
    ),
    click.option(
        "--external-exasol-xmlrpc-port",
        type=int,
        default=443,
        show_default=True,
        help="""Port for the xmlrpc server""",
    ),
    click.option(
        "--external-exasol-xmlrpc-user",
        type=str,
        default="""admin""",
        show_default=True,
        help="""User for the xmlrpc server""",
    ),
    click.option(
        "--external-exasol-xmlrpc-password",
        type=str,
        help="""Password for the xmlrpc server""",
    ),
    click.option(
        "--external-exasol-xmlrpc-cluster-name",
        type=str,
        default="""cluster1""",
        show_default=True,
        help="""Password for the xmlrpc server""",
    ),
]
