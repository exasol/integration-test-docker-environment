from typing import Optional

from exasol_integration_test_docker_environment.testing.exaslct_docker_test_environment import \
    ExaslctDockerTestEnvironment


class SpawnedTestEnvironments:
    def __init__(self, on_host_environment: ExaslctDockerTestEnvironment,
                 google_cloud_environment: Optional[ExaslctDockerTestEnvironment]):
        self.on_host_docker_environment = on_host_environment
        self.google_cloud_environment = google_cloud_environment

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self.on_host_docker_environment is not None:
            self.on_host_docker_environment.close()

        if self.google_cloud_environment is not None:
            self.google_cloud_environment.close()
