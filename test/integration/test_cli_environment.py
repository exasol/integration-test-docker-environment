from inspect import cleandoc
from test.integration.helpers import get_executor_factory
from typing import (
    List,
    Optional,
)

import docker
import pytest

from exasol_integration_test_docker_environment.lib.base.db_os_executor import (
    DbOsExecFactory,
)
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.test_environment.database_setup.find_exaplus_in_db_container import (
    find_exaplus,
)
from exasol_integration_test_docker_environment.lib.test_environment.parameter.docker_db_test_environment_parameter import (
    DbOsAccess,
)
from exasol_integration_test_docker_environment.testing.exaslct_docker_test_environment import (
    ExaslctDockerTestEnvironment,
)
from exasol_integration_test_docker_environment.testing.spawned_test_environments import (
    SpawnedTestEnvironments,
)


class NumberCheck:
    def __init__(self, db: SpawnedTestEnvironments, all: list[str]) -> None:
        self.db = db
        self.all = all

    def count(self, selected: Optional[list[str]] = None):
        return len(selected if selected is not None else self.all)

    @property
    def log(self) -> str:
        assert self.db.on_host_docker_environment.completed_process
        return self.db.on_host_docker_environment.completed_process.stdout.decode(
            "utf8"
        )

    def fail(self, prefix) -> str:
        return cleandoc(
            f"""
            {prefix} in {self.all}.
            Startup log was:
            {self.log}
            """
        )


def smoke_test_sql(exaplus_path: str, env: ExaslctDockerTestEnvironment) -> str:
    def quote(s):
        return f"'{s}'"

    assert env.environment_info
    db_info = env.environment_info.database_info
    command: list[str] = [
        str(exaplus_path),
        "-c",
        quote(f"{db_info.host}:{db_info.ports.database}"),
        "-u",
        quote(env.db_username),
        "-p",
        quote(env.db_password),
    ]
    command += [
        "-sql",
        quote("select 1;"),
        "-jdbcparam",
        "validateservercertificate=0",
    ]
    command_str = " ".join(command)
    return f'bash -c "{command_str}" '


def test_db_container_started(cli_context):
    with cli_context() as db:
        with ContextDockerClient() as docker_client:
            name = db.on_host_docker_environment.name
            containers = [
                c.name for c in docker_client.containers.list() if name in c.name
            ]
            check = NumberCheck(db, containers)
            assert check.count() == 1, check.fail("Not exactly 1 container")

            db_containers = [c for c in containers if "db_container" in c]
            check = NumberCheck(db, containers)
            assert check.count(db_containers) == 1, check.fail("Found no db container")


@pytest.mark.parametrize("db_os_access", [DbOsAccess.DOCKER_EXEC, DbOsAccess.SSH])
def test_db_available(cli_context, fabric_stdin, db_os_access):
    params = ["--db-os-access", db_os_access.name]
    with cli_context(additional_parameters=params) as db:
        with ContextDockerClient() as docker_client:
            dbinfo = db.on_host_docker_environment.environment_info.database_info
            db_container_name = dbinfo.container_info.container_name
            db_container = docker_client.containers.get(db_container_name)
            executor_factory = get_executor_factory(dbinfo, db_os_access)
            with executor_factory.executor() as executor:
                executor.prepare()
                exaplus = find_exaplus(db_container, executor)
                command = smoke_test_sql(exaplus, db.on_host_docker_environment)
                exit_code, output = db_container.exec_run(command)
                assert (
                    exit_code == 0
                ), f"Error while executing 'exaplus' in test container. Got output:\n {output}"
