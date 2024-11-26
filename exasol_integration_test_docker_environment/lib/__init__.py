def extract_modulename_for_build_steps(path: str):
    return path.replace("/", "_").replace(".", "_")


PACKAGE_NAME = "exasol_integration_test_docker_environment"
