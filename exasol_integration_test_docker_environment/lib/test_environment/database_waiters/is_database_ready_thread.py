import time
from threading import Thread

from docker.models.containers import Container

from exasol_integration_test_docker_environment.lib.data.database_credentials import DatabaseCredentials
from exasol_integration_test_docker_environment.lib.data.database_info import DatabaseInfo


class IsDatabaseReadyThread(Thread):

    def __init__(self,
                 logger,
                 database_info: DatabaseInfo,
                 database_container: Container,
                 database_credentials: DatabaseCredentials,
                 docker_db_image_version: str):
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

    def stop(self):
        self.logger.info("Stop IsDatabaseReadyThread")
        self.finish = True

    def run(self):
        db_connection_command = self.create_db_connection_command()
        bucket_fs_connection_command = self.create_bucketfs_connection_command()
        while not self.finish:
            (exit_code_db_connection, self.output_db_connection) = \
                self._db_container.exec_run(cmd=db_connection_command)
            (exit_code_bucketfs_connection, self.output_bucketfs_connection) = \
                self._db_container.exec_run(cmd=bucket_fs_connection_command)
            if exit_code_db_connection == 0 and exit_code_bucketfs_connection == 0:
                self.finish = True
                self.is_ready = True
            time.sleep(1)

    def create_db_connection_command(self):
        username = self.database_credentials.db_user
        password = self.database_credentials.db_password
        connection_options = f"""-c 'localhost:{self._database_info.db_port}' -u '{username}' -p '{password}'"""

        exaplus = f"/usr/opt/EXASuite-7/EASolution-{self.docker_db_image_version}/bin/Console/exaplus"
        cmd = f"""{exaplus} {connection_options}  -sql 'select 1;' -jdbcparam 'validateservercertificate=0'"""
        bash_cmd = f"""bash -c "{cmd}" """
        return bash_cmd

    def create_bucketfs_connection_command(self):
        username = "w"
        password = self.database_credentials.bucketfs_write_password
        cmd = f"""curl --silent --show-error --fail '{username}:{password}@localhost:{self._database_info.bucketfs_port}'"""
        bash_cmd = f"""bash -c "{cmd}" """
        return bash_cmd
