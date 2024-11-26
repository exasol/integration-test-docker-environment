from typing import (
    List,
    Optional,
)

import luigi
from luigi import Config

from exasol_integration_test_docker_environment.lib.test_environment.parameter.test_container_parameter import (
    OptionalTestContainerParameter,
)


class GeneralSpawnTestEnvironmentParameter(OptionalTestContainerParameter):
    reuse_database_setup: bool = luigi.BoolParameter(False, significant=False)  # type: ignore
    reuse_test_container: bool = luigi.BoolParameter(False, significant=False)  # type: ignore
    no_test_container_cleanup_after_success: bool = luigi.BoolParameter(False, significant=False)  # type: ignore
    no_test_container_cleanup_after_failure: bool = luigi.BoolParameter(False, significant=False)  # type: ignore
    max_start_attempts: int = luigi.IntParameter(2, significant=False)  # type: ignore
    docker_runtime: Optional[str] = luigi.OptionalParameter(None, significant=False)  # type: ignore
    create_certificates: bool = luigi.BoolParameter()  # type: ignore
    additional_db_parameter: List[str] = luigi.ListParameter()  # type: ignore
