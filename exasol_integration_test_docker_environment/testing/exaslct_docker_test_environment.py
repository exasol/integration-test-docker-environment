import subprocess
from typing import Optional

from exasol_integration_test_docker_environment.lib.data.environment_info import EnvironmentInfo


class ExaslctDockerTestEnvironment:
    def __init__(self, name: str, database_host: str,
                 db_username: str, db_password: str,
                 bucketfs_username: str, bucketfs_password: str,
                 database_port: int, bucketfs_port: int,
                 environment_info: Optional[EnvironmentInfo] = None,
                 completed_process: Optional[subprocess.CompletedProcess] = None):
        self.db_password = db_password
        self.db_username = db_username
        self.database_port = database_port
        self.bucketfs_port = bucketfs_port
        self.bucketfs_username = bucketfs_username
        self.bucketfs_password = bucketfs_password
        self.database_host = database_host
        self.name = name
        self.environment_info = environment_info
        self.completed_process = completed_process
        self.clean_up = None

    def close(self):
        if self.clean_up is not None:
            self.clean_up()
