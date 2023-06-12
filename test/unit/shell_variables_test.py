import contextlib
import pytest

from inspect import cleandoc
from unittest.mock import Mock
from exasol_integration_test_docker_environment \
    .lib.test_environment.shell_variables import ShellVariables
from exasol_integration_test_docker_environment \
    .lib.test_environment.ports import Ports


def test_render_with_prefix():
    actual = ShellVariables({"A": "1"}).render("export ")
    assert actual == "export ENVIRONMENT_A=1\n"


def test_from_test_environment_info():
    container_info = Mock(
        network_aliases = ["cna-1", "cna-2"],
        container_name = "container-name",
        ip_address = "container-ip",
        volume_name = "container-volume",
    )
    database_info = Mock(
        host = "db-host",
        ports = Ports(1,2,3),
        container_info = container_info,
    )
    test_container_info = Mock(
        network_aliases = ["tcna-1", "tcna-2"],
        ip_address = "tc-ip",
    )
    test_environment = Mock(
        type = "type",
        database_info = database_info,
        test_container_info = test_container_info,
    )
    test_environment.name = "name"

    actual = ShellVariables.from_test_environment_info(
        "test-container-name",
        "ip-address",
        test_environment,
    )
    assert actual.render().strip() == cleandoc("""
        ENVIRONMENT_NAME=name
        ENVIRONMENT_TYPE=type
        ENVIRONMENT_DATABASE_HOST=db-host
        ENVIRONMENT_DATABASE_DB_PORT=1
        ENVIRONMENT_DATABASE_BUCKETFS_PORT=2
        ENVIRONMENT_DATABASE_SSH_PORT=3
        ENVIRONMENT_DATABASE_CONTAINER_NAME=container-name
        ENVIRONMENT_DATABASE_CONTAINER_NETWORK_ALIASES="cna-1 cna-2"
        ENVIRONMENT_DATABASE_CONTAINER_IP_ADDRESS=container-ip
        ENVIRONMENT_DATABASE_CONTAINER_VOLUMNE_NAME=container-volume
        ENVIRONMENT_DATABASE_CONTAINER_DEFAULT_BRIDGE_IP_ADDRESS=ip-address
        ENVIRONMENT_TEST_CONTAINER_NAME=test-container-name
        ENVIRONMENT_TEST_CONTAINER_NETWORK_ALIASES="tcna-1 tcna-2"
        ENVIRONMENT_TEST_CONTAINER_IP_ADDRESS=tc-ip
        """)
