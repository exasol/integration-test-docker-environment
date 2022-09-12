import time
from pathlib import PurePath
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

    def _find_exaplus(self) -> PurePath:
        exit, output = self._db_container.exec_run(cmd="find /usr/opt -type f -name 'exaplus'")
        if exit != 0:
            self.finish = True
            raise RuntimeError("Exaplus not found on docker db!")
        found_paths = list(filter(None, output.decode("UTF-8").split("\n")))
        if len(found_paths) != 1:
            self.finish = True
            raise RuntimeError(f"Error determining exaplus path! Output is {output}")
        exaplus_path = PurePath(found_paths[0])
        exit, output = self._db_container.exec_run(cmd=f"{exaplus_path} --help")
        if exit != 0:
            self.finish = True
            raise RuntimeError(f"Exaplus not working as expected! Output is {output}")
        return exaplus_path

    def run(self):
        exaplus_path = self._find_exaplus()
        db_connection_command = self.create_db_connection_command(exaplus_path)
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

    def create_db_connection_command(self, exaplus_path: PurePath):
        username = self.database_credentials.db_user
        password = self.database_credentials.db_password
        connection_options = f"""-c 'localhost:{self._database_info.db_port}' -u '{username}' -p '{password}'"""

        cmd = f"""{exaplus_path} {connection_options}  -sql 'select 1;' -jdbcparam 'validateservercertificate=0'"""
        bash_cmd = f"""bash -c "{cmd}" """
        return bash_cmd

    def create_bucketfs_connection_command(self):
        username = "w"
        password = self.database_credentials.bucketfs_write_password
        cmd = f"""curl --silent --show-error --fail '{username}:{password}@localhost:{self._database_info.bucketfs_port}'"""
        bash_cmd = f"""bash -c "{cmd}" """
        return bash_cmd
