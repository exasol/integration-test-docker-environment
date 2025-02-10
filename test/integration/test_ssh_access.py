import contextlib
from test.integration.helpers import (
    container_named,
    get_executor_factory,
    normalize_request_name,
)

import docker
import fabric
import pytest
from docker.models.containers import Container as DockerContainer

from exasol_integration_test_docker_environment.lib.base.ssh_access import (
    SshKey,
    SshKeyCache,
)
from exasol_integration_test_docker_environment.lib.models.data.container_info import (
    ContainerInfo,
)
from exasol_integration_test_docker_environment.lib.models.data.database_info import (
    DatabaseInfo,
)
from exasol_integration_test_docker_environment.lib.models.data.ssh_info import SshInfo
from exasol_integration_test_docker_environment.lib.test_environment.parameter.docker_db_test_environment_parameter import (
    DbOsAccess,
)
from exasol_integration_test_docker_environment.lib.test_environment.ports import (
    Ports,
    find_free_ports,
)


def test_generate_ssh_key_file(api_database):
    params = {"db_os_access": "SSH"}
    with api_database(additional_parameters=params) as db:
        cache = SshKeyCache()
        container_name = db.environment_info.database_info.container_info.container_name
        with container_named(container_name) as container:
            command = container.exec_run("cat /root/.ssh/authorized_keys")
    assert cache.private_key.exists()
    assert " itde-ssh-access" in command[1].decode("utf-8")


def test_ssh_access(api_database, fabric_stdin):
    params = {"db_os_access": "SSH"}
    with api_database(additional_parameters=params) as db:
        container_name = db.environment_info.database_info.container_info.container_name
        with container_named(container_name) as container:
            command = container.exec_run("cat /root/.ssh/authorized_keys")
        key = SshKey.from_cache()
        result = fabric.Connection(
            f"root@localhost:{db.ports.ssh}",
            connect_kwargs={"pkey": key.private},
        ).run("ls /exa/etc/EXAConf")
        assert result.stdout == "/exa/etc/EXAConf\n"


@pytest.fixture
def sshd_container(request):
    testname = normalize_request_name(request.node.name)

    @contextlib.contextmanager
    def create_context(ssh_port_forward: int, public_key: str) -> DockerContainer:
        client = docker.from_env()
        container = client.containers.run(
            name=testname,
            image="linuxserver/openssh-server:9.3_p2-r0-ls123",
            detach=True,
            ports={"2222/tcp": ssh_port_forward},
            environment={"PUBLIC_KEY": public_key},
        )
        try:
            yield container
        finally:
            container.stop()
            container.remove()

    return create_context


@pytest.mark.parametrize("db_os_access", [DbOsAccess.SSH, DbOsAccess.DOCKER_EXEC])
def test_db_os_executor_factory(sshd_container, db_os_access, fabric_stdin):
    def database_info(container_name, ssh_port_forward):
        ssh_info = SshInfo(
            user="linuxserver.io",
            key_file=SshKeyCache().private_key,
        )
        return DatabaseInfo(
            host="localhost",
            ports=Ports(-1, -1, ssh_port_forward),
            reused=False,
            container_info=ContainerInfo(
                container_name=container_name,
                ip_address=None,
                network_aliases=[],
                network_info=None,
            ),
            ssh_info=ssh_info,
        )

    ssh_port_forward = find_free_ports(1)[0]
    public_key = SshKey.from_cache().public_key_as_string()
    with sshd_container(ssh_port_forward, public_key) as container:
        dbinfo = database_info(container.name, ssh_port_forward)
        factory = get_executor_factory(dbinfo, ssh_port_forward)
        with factory.executor() as executor:
            exit_code, output = executor.exec("ls /keygen.sh")
    output = output.decode("utf-8").strip()
    assert (exit_code, output) == (0, "/keygen.sh")
