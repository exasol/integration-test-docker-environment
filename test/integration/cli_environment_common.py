from inspect import cleandoc
from test.integration.helpers import get_executor_factory
from typing import (
    Any,
    cast,
)

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.test_environment.database_setup.find_exaplus_in_db_container import (
    find_exaplus,
)
from exasol_integration_test_docker_environment.lib.test_environment.parameter.docker_db_test_environment_parameter import (
    DbOsAccess,
)
from exasol_integration_test_docker_environment.testing.cli_test_environment_context_provider import (
    CliContextProvider,
)
from exasol_integration_test_docker_environment.testing.exaslct_docker_test_environment import (
    ExaslctDockerTestEnvironment,
)
from exasol_integration_test_docker_environment.testing.spawned_test_environments import (
    SpawnedTestEnvironments,
)


class NumberCheck:
    def __init__(self, db: SpawnedTestEnvironments, all_names: list[str]) -> None:
        self.db = db
        self.all_names = all_names

    def count(self, selected: list[str] | None = None) -> int:
        return len(selected if selected is not None else self.all_names)

    @property
    def log(self) -> str:
        assert self.db.on_host_docker_environment.completed_process
        return self.db.on_host_docker_environment.completed_process.stdout.decode(
            "utf8"
        )

    def fail(self, prefix: str) -> str:
        return cleandoc(f"""
            {prefix} in {self.all_names}.
            Startup log was:
            {self.log}
            """)


def smoke_test_sql(exaplus_path: str, env: ExaslctDockerTestEnvironment) -> str:
    def quote(value: str) -> str:
        return f"'{value}'"

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


def assert_db_container_started(context: CliContextProvider) -> None:
    with context(None, None) as db:
        with ContextDockerClient() as docker_client:
            name = db.on_host_docker_environment.name
            containers = [
                container.name
                for container in docker_client.containers.list()
                if name in container.name
            ]
            check = NumberCheck(db, containers)
            assert check.count() == 1, check.fail("Not exactly 1 container")

            db_containers = [
                container for container in containers if "db_container" in container
            ]
            assert check.count(db_containers) == 1, check.fail("Found no db container")


def build_additional_parameters(
    db_os_access: DbOsAccess, create_certificates: bool
) -> list[str]:
    params = ["--db-os-access", db_os_access.name]
    if create_certificates:
        params.append("--create-certificates")
    return params


def assert_db_available(
    context: CliContextProvider,
    db_os_access: DbOsAccess,
    create_certificates: bool,
) -> None:
    params = build_additional_parameters(db_os_access, create_certificates)
    with context("db_avail", params) as db:
        with ContextDockerClient() as docker_client:
            assert db.on_host_docker_environment.environment_info
            dbinfo = db.on_host_docker_environment.environment_info.database_info
            assert dbinfo.container_info
            db_container_name = dbinfo.container_info.container_name
            db_container = docker_client.containers.get(db_container_name)
            executor_factory = get_executor_factory(dbinfo, db_os_access)
            with cast(Any, executor_factory.executor()) as executor:
                executor.prepare()
                exaplus = find_exaplus(db_container, executor)
                command = smoke_test_sql(str(exaplus), db.on_host_docker_environment)
                exit_code, output = db_container.exec_run(command)
                assert exit_code == 0, (
                    "Error while executing 'exaplus' in test container. "
                    f"Got output:\n {output}"
                )
