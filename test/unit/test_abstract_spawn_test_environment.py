import contextlib
import pytest

from inspect import cleandoc
from unittest.mock import MagicMock, Mock
from exasol_integration_test_docker_environment \
    .lib.test_environment.abstract_spawn_test_environment import AbstractSpawnTestEnvironment
from exasol_integration_test_docker_environment \
    .lib.test_environment.ports import Ports


def test_AbstractSpawnTestEnvironment():
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
        container_name = "test-container-name",
        network_aliases = ["tcna-1", "tcna-2"],
        ip_address = "tc-ip",
    )
    test_environment = Mock(
        type = "type",
        database_info = database_info,
        test_container_info = test_container_info,
    )
    test_environment.name = "name"

    @contextlib.contextmanager
    def docker_client_context():
        container = Mock(attrs={"NetworkSettings": {"Networks": {"bridge": {"IPAddress": "ip-address"}}}})
        all_containers = Mock(get = MagicMock(return_value=container))
        yield Mock(containers = all_containers)

    testee = AbstractSpawnTestEnvironment(
        job_id="1",
        db_user="user",
        db_password="password",
        bucketfs_write_password="w",
        test_container_content="",
        additional_db_parameter="",
        environment_name="env",
    )
    testee._get_docker_client = MagicMock(return_value=docker_client_context())
    actual = testee.collect_shell_variables(test_environment)
    assert actual.render().strip() == cleandoc("""
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
        """)
