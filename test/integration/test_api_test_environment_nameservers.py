from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient


def _assert_nameserver(container_name, nameservers: str):
    with ContextDockerClient() as docker_client:
        containers = [
            c.name for c in docker_client.containers.list() if container_name in c.name
        ]
        db_container = [c for c in containers if "db_container" in c]
        exit_result = docker_client.containers.get(db_container[0]).exec_run(
            "cat /exa/etc/EXAConf"
        )
        output = exit_result[1].decode("UTF-8")
        if output == "":
            exit_result = docker_client.containers.get(db_container[0]).exec_run(
                "cat /exa/etc/EXAConf"
            )
            output = exit_result[1].decode("UTF-8")
            return_code = exit_result[0]
        return_code = exit_result[0]
        assert return_code == 0
        assert f"NameServers = {nameservers}" in output


def test_no_nameserver(api_context):
    with api_context() as db:
        _assert_nameserver(db.environment_info.name, "")


def test_single_nameserver(api_context):
    additional_parameters = {"nameserver": ("8.8.8.8",)}
    with api_context(
        additional_parameters=additional_parameters,
    ) as db:
        _assert_nameserver(db.environment_info.name, "8.8.8.8")


def test_multiple_nameserver(api_context):
    additional_parameters = {"nameserver": ("8.8.8.8", "8.8.8.9")}
    with api_context(
        additional_parameters=additional_parameters,
    ) as db:
        _assert_nameserver(db.environment_info.name, "8.8.8.8,8.8.8.9")
