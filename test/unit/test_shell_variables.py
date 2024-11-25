import contextlib
from inspect import cleandoc
from unittest.mock import Mock

import pytest

from exasol_integration_test_docker_environment.lib.test_environment.ports import Ports
from exasol_integration_test_docker_environment.lib.test_environment.shell_variables import (
    ShellVariables,
)


def test_render_with_prefix():
    actual = ShellVariables({"A": "1"}).render("export ")
    assert actual == "export ITDE_A=1\n"


def test_from_test_environment_info():
    container_info = Mock(
        network_aliases=["cna-1", "cna-2"],
        container_name="container-name",
        ip_address="container-ip",
        volume_name="container-volume",
    )
    database_info = Mock(
        host="db-host",
        ports=Ports(1, 2, 3),
        container_info=container_info,
    )
    test_container_info = Mock(
        container_name="test-container-name",
        network_aliases=["tcna-1", "tcna-2"],
        ip_address="tc-ip",
    )
    test_environment = Mock(
        type="type",
        database_info=database_info,
        test_container_info=test_container_info,
    )
    test_environment.name = "name"

    actual = ShellVariables.from_test_environment_info(
        "ip-address",
        test_environment,
    )
    assert actual.render().strip() == cleandoc(
        """
        ITDE_NAME=name
        ITDE_TYPE=type
        ITDE_DATABASE_HOST=db-host
        ITDE_DATABASE_DB_PORT=1
        ITDE_DATABASE_BUCKETFS_PORT=2
        ITDE_DATABASE_SSH_PORT=3
        ITDE_DATABASE_CONTAINER_NAME=container-name
        ITDE_DATABASE_CONTAINER_NETWORK_ALIASES="cna-1 cna-2"
        ITDE_DATABASE_CONTAINER_IP_ADDRESS=container-ip
        ITDE_DATABASE_CONTAINER_VOLUMNE_NAME=container-volume
        ITDE_DATABASE_CONTAINER_DEFAULT_BRIDGE_IP_ADDRESS=ip-address
        ITDE_TEST_CONTAINER_NAME=test-container-name
        ITDE_TEST_CONTAINER_NETWORK_ALIASES="tcna-1 tcna-2"
        ITDE_TEST_CONTAINER_IP_ADDRESS=tc-ip
        """
    )
