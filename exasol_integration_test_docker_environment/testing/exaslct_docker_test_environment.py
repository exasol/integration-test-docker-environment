import subprocess
from typing import Optional

from exasol_integration_test_docker_environment.cli.options.test_environment_options import (
    LATEST_DB_VERSION,
)
from exasol_integration_test_docker_environment.lib.data.environment_info import (
    EnvironmentInfo,
)
from exasol_integration_test_docker_environment.lib.test_environment.ports import Ports
from exasol_integration_test_docker_environment.testing.utils import (
    check_db_version_from_env,
)


class ExaslctDockerTestEnvironment:
    def __init__(
        self,
        name: str,
        database_host: str,
        db_username: str,
        db_password: str,
        bucketfs_username: str,
        bucketfs_password: str,
        ports: Ports,
        environment_info: Optional[EnvironmentInfo] = None,
        completed_process: Optional[subprocess.CompletedProcess] = None,
    ):
        self.db_password = db_password
        self.db_username = db_username
        self.ports = ports
        self.bucketfs_username = bucketfs_username
        self.bucketfs_password = bucketfs_password
        self.database_host = database_host
        self.name = name
        self.environment_info = environment_info
        self.completed_process = completed_process
        self.clean_up = None
        self.docker_db_image_version = check_db_version_from_env() or LATEST_DB_VERSION

    def close(self):
        if self.clean_up is not None:
            self.clean_up()
