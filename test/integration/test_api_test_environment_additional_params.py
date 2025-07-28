from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient

ADDITIONAL_DB_PARAMS = ["-disableIndexIteratorScan=1", "-disableIndexIteratorScan=1"]


def test_additional_params_are_used(api_context):
    additional_db_parameters = {
        "additional_db_parameter": tuple(add_db_param for add_db_param in ADDITIONAL_DB_PARAMS)
    }
    with api_context(
        additional_parameters=additional_db_parameters,
    ) as db:
        with ContextDockerClient() as docker_client:
            db_container = docker_client.containers.get(
                db.environment_info.database_info.container_info.container_name
            )
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
            params_line = params_lines[0]
            for add_db_param in ADDITIONAL_DB_PARAMS:
                assert add_db_param in params_line
