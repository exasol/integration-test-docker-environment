import pytest

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient

def _get_db_parameter_line_from_dwad_client(container_name: str) -> str:
    """
    Run `dwad_client` in the DB container to get the db parameter line
    DWAD client is expected to report only a single line starting with "Parameters:"
    Args:
        container_name:

    Returns:

    """
    with ContextDockerClient() as docker_client:
        db_container = docker_client.containers.get(container_name)
        exit_code, output = db_container.exec_run("dwad_client print-params DB1")
        assert exit_code == 0, (
            f"Error while executing 'dwad_client' "
            f"in db container got output\n {output.decode('UTF-8')}."
        )

        params_lines = [
            line
            for line in output.decode("UTF-8").splitlines()
            if line.startswith("Parameters:")
        ]
        assert len(params_lines) == 1, "Unexpected format of output of dwad_client"
        return params_lines[0]


@pytest.mark.parametrize("additional_db_parameters", (("-disableIndexIteratorScan=1", "-disableViewOptimization=1"),
                                                      ("-disableIndexIteratorScan=1", "-disableIndexIteratorScan=1")))
def test_additional_params_are_used(api_context, additional_db_parameters):
    """
    This test checks that running "spawn_test_environment" works as expected with parameter "additional_db_parameter".
    The tool "dwad_client" is used then to query if the database was started with expected parameters.
    Args:
        api_context:
        additional_db_parameters:

    Returns:

    """
    additional_parameters = { "additional_db_parameter": additional_db_parameters }
    with api_context(
        additional_parameters=additional_parameters,
    ) as db:
        parameter_line = _get_db_parameter_line_from_dwad_client(db.environment_info.database_info.container_info.container_name)
        for add_db_param in additional_db_parameters:
            assert add_db_param in parameter_line
