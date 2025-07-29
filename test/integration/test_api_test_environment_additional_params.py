from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient

# why does this list contain the same parameter 2 times?
ADDITIONAL_DB_PARAMS = ["-disableIndexIteratorScan=1", "-disableIndexIteratorScan=1"]


def get_output_line_with_prefix(
    docker_container_name: str,
    command: str,
    prefix: str = "",
) -> str:
    """
    Execute the specified command in the specified Docker container and
    return the line from the command's output, starting with the specified
    prefix. Assert there is exactly one such line.
    """
    with ContextDockerClient() as docker_client:
        container = docker_client.containers.get(container_name)
        exit_code, output = container.exec_run(command)
        decoded = output.decode("UTF-8")
        assert exit_code == 0, (
            f"Error while executing '{command}' "
            f"in db container got output\n {decoded}."
        )
        filtered = [x for x in decoded.splitlines() if x.startswith(filter)]
        assert len(filtered) == 1, f"Unexpected output of {command}: {filtered}"
        return filtered[0]


def test_additional_params_are_used(api_context):
    additional_db_parameters = {
        "additional_db_parameter": tuple(
            add_db_param for add_db_param in ADDITIONAL_DB_PARAMS
        )
    }
    with api_context(
        additional_parameters=additional_db_parameters,
    ) as db:
        dwad_parameters = get_output_line_with_prefix(
            container_name=db.environment_info.database_info.container_info.container_name,
            command="dwad_client print-params DB1",
            prefix="Parameters:",
        )
        for param in ADDITIONAL_DB_PARAMS:
            assert param in dwad_parameters
