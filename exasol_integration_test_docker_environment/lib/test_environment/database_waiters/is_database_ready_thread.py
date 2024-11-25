import time
from logging import Logger
from pathlib import PurePath
from threading import Thread

from docker.models.containers import Container

from exasol_integration_test_docker_environment.lib.base.db_os_executor import (
    DbOsExecFactory,
)
from exasol_integration_test_docker_environment.lib.data.database_credentials import (
    DatabaseCredentials,
)
from exasol_integration_test_docker_environment.lib.data.database_info import (
    DatabaseInfo,
)
from exasol_integration_test_docker_environment.lib.test_environment.database_setup.find_exaplus_in_db_container import (
    find_exaplus,
)


class IsDatabaseReadyThread(Thread):
    def __init__(
        self,
        logger: Logger,
        database_info: DatabaseInfo,
        database_container: Container,
        database_credentials: DatabaseCredentials,
        docker_db_image_version: str,
        executor_factory: DbOsExecFactory,
    ):
        super().__init__()
        self.logger = logger
        self.database_credentials = database_credentials
        self._database_info = database_info
        self._db_container = database_container
        self.finish = False
        self.is_ready = False
        self.output_db_connection = None
        self.output_bucketfs_connection = None
        self.docker_db_image_version = docker_db_image_version
        self.executor_factory = executor_factory

    def stop(self):
        self.logger.info("Stop IsDatabaseReadyThread")
        self.finish = True

    def run(self):
        try:
            with self.executor_factory.executor() as executor:
                db_connection_command = ""
                bucket_fs_connection_command = ""
                try:
                    executor.prepare()
                    exaplus_path = find_exaplus(self._db_container, executor)
                    db_connection_command = self.create_db_connection_command(
                        exaplus_path
                    )
                    bucket_fs_connection_command = (
                        self.create_bucketfs_connection_command()
                    )
                except RuntimeError as e:
                    self.logger.exception(
                        "Caught exception while searching for exaplus."
                    )
                    self.finish = True
                while not self.finish:
                    (exit_code_db_connection, self.output_db_connection) = (
                        executor.exec(db_connection_command)
                    )
                    (exit_code_bucketfs_connection, self.output_bucketfs_connection) = (
                        executor.exec(bucket_fs_connection_command)
                    )
                    if (
                        exit_code_db_connection == 0
                        and exit_code_bucketfs_connection == 0
                    ):
                        self.finish = True
                        self.is_ready = True
                    time.sleep(1)
        except Exception as e:
            self.finish = True
            self.logger.exception("Caught exception in IsDatabaseReadyThread.run.")

    def create_db_connection_command(self, exaplus_path: PurePath):
        username = self.database_credentials.db_user
        password = self.database_credentials.db_password
        connection_options = f"""-c 'localhost:{self._database_info.ports.database}' -u '{username}' -p '{password}'"""

        cmd = f"""{exaplus_path} {connection_options} -sql 'select 1;' -jdbcparam 'validateservercertificate=0'"""
        bash_cmd = f"""bash -c "{cmd}" """
        return bash_cmd

    def create_bucketfs_connection_command(self):
        username = "w"
        password = self.database_credentials.bucketfs_write_password
        cmd = f"""curl --silent --show-error --fail '{username}:{password}@localhost:{self._database_info.ports.bucketfs}'"""
        bash_cmd = f"""bash -c "{cmd}" """
        return bash_cmd
