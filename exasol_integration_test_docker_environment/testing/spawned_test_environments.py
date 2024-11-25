from typing import Optional

from exasol_integration_test_docker_environment.testing.exaslct_docker_test_environment import (
    ExaslctDockerTestEnvironment,
)


class SpawnedTestEnvironments:
    def __init__(
        self,
        on_host_environment: ExaslctDockerTestEnvironment,
        slc_test_run_environment: Optional[ExaslctDockerTestEnvironment],
    ):
        self.on_host_docker_environment = on_host_environment
        self.slc_test_run_environment = slc_test_run_environment

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self.on_host_docker_environment is not None:
            self.on_host_docker_environment.close()

        if self.slc_test_run_environment is not None:
            self.slc_test_run_environment.close()
