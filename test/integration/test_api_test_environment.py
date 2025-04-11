from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.testing.utils import find_docker_container_names


def test_environment_info_set(api_default_database_with_test_conainer_module):
    assert api_default_database_with_test_conainer_module.environment_info is not None


def test_all_containers_started(api_default_database_with_test_conainer_module):
    test_environment = api_default_database_with_test_conainer_module
    containers = find_docker_container_names(test_environment.name)
    assert len(containers) == 2, f"Not exactly 2 containers in {containers}."
    db_container = [c for c in containers if "db_container" in c]
    assert len(db_container) == 1, f"Found no db container in {containers}."
    test_container = [c for c in containers if "test_container" in c]
    assert len(test_container) == 1, f"Found no test container in {containers}."


def test_docker_available_in_test_container(
    api_default_database_with_test_conainer_module,
):
    environment_info = api_default_database_with_test_conainer_module.environment_info
    with ContextDockerClient() as docker_client:
        test_container = docker_client.containers.get(
            environment_info.test_container_info.container_name
        )
        exit_result = test_container.exec_run("docker ps")
        exit_code = exit_result[0]
        output = exit_result[1]
        assert (
            exit_code == 0
        ), f"Error while executing 'docker ps' in test container got output\n {output}."


def test_db_container_available(api_default_database_with_test_conainer_module):
    environment_info = api_default_database_with_test_conainer_module.environment_info
    with ContextDockerClient() as docker_client:
        db_container = docker_client.containers.get(
            environment_info.database_info.container_info.container_name
        )
        exit_result = db_container.exec_run("ls /exa")
        exit_code = exit_result[0]
        output = exit_result[1]
        assert (
            exit_code == 0
        ), f"Error while executing 'ls /exa' in db container got output\n {output}."


def test_db_available(api_default_database_with_test_conainer_module):
    test_environment = api_default_database_with_test_conainer_module
    environment_info = test_environment.environment_info
    with ContextDockerClient() as docker_client:
        test_container = docker_client.containers.get(
            environment_info.test_container_info.container_name
        )
        exit_result = test_container.exec_run(
            create_db_connection_command(test_environment)
        )
        exit_code = exit_result[0]
        output = exit_result[1]
        assert (
            exit_code == 0
        ), f"Error while executing 'exaplus' in test container got output\n {output}."


def create_db_connection_command(test_environment):
    username = test_environment.db_username
    password = test_environment.db_password
    db_host = test_environment.environment_info.database_info.host
    db_port = test_environment.environment_info.database_info.ports.database
    connection_options = f"-c '{db_host}:{db_port}' -u '{username}' -p '{password}'"
    cmd = f"""$EXAPLUS {connection_options}  -sql 'select 1;' -jdbcparam 'validateservercertificate=0'"""
    bash_cmd = f"""bash -c "{cmd}" """
    return bash_cmd


def test_build_mapping(api_default_database_with_test_conainer_module):
    environment_info = api_default_database_with_test_conainer_module.environment_info
    with ContextDockerClient() as docker_client:
        test_container = docker_client.containers.get(
            environment_info.test_container_info.container_name
        )
        exit_code, output = test_container.exec_run("cat /test.text")
        assert exit_code == 0
        assert output.decode("UTF-8") == "Empty File"
