from typing import (
    Optional,
)

import luigi

from exasol_integration_test_docker_environment.lib.test_environment.parameter.test_container_parameter import (
    OptionalTestContainerParameter,
)


class GeneralSpawnTestEnvironmentParameter(OptionalTestContainerParameter):
    reuse_database_setup: bool = luigi.BoolParameter(False, significant=False)
    reuse_test_container: bool = luigi.BoolParameter(False, significant=False)
    no_test_container_cleanup_after_success: bool = luigi.BoolParameter(
        False, significant=False
    )
    no_test_container_cleanup_after_failure: bool = luigi.BoolParameter(
        False, significant=False
    )
    max_start_attempts: int = luigi.IntParameter(2, significant=False)
    docker_runtime: Optional[str] = luigi.OptionalParameter(None, significant=False)
    create_certificates: bool = luigi.BoolParameter()
    additional_db_parameter: tuple[str, ...] = luigi.ListParameter()
    docker_environment_variables: tuple[str, ...] = luigi.ListParameter()
