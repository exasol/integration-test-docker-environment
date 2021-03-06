import logging
from pathlib import Path

import luigi

from exasol_integration_test_docker_environment.lib.base.docker_base_task import DockerBaseTask
from exasol_integration_test_docker_environment.lib.base.json_pickle_parameter import JsonPickleParameter
from exasol_integration_test_docker_environment.lib.data.database_credentials import DatabaseCredentialsParameter
from exasol_integration_test_docker_environment.lib.data.environment_info import EnvironmentInfo


class PopulateEngineSmallTestDataToDatabase(DockerBaseTask, DatabaseCredentialsParameter):
    logger = logging.getLogger('luigi-interface')

    environment_name = luigi.Parameter()
    reuse_data = luigi.BoolParameter(False, significant=False)
    test_environment_info = JsonPickleParameter(
        EnvironmentInfo, significant=False)  # type: EnvironmentInfo

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._test_container_info = self.test_environment_info.test_container_info
        self._database_info = self.test_environment_info.database_info

    def run_task(self):
        if not self.reuse_data:
            self.populate_data()
        else:
            self.logger.warning("Reusing data")
            self.write_logs("Reused")

    def populate_data(self):
        self.logger.warning("Uploading data")
        username = self.db_user
        password = self.db_password
        test_container = self._client.containers.get(self._test_container_info.container_name)
        cmd = f"""cd /tests/test/enginedb_small; $EXAPLUS -c '{self._database_info.host}:{self._database_info.db_port}' -u '{username}' -p '{password}' -f import.sql"""
        bash_cmd = f"""bash -c "{cmd}" """
        exit_code, output = test_container.exec_run(cmd=bash_cmd)
        self.write_logs(output.decode("utf-8"))
        if exit_code != 0:
            raise Exception("Failed to populate the database with data.\nLog: %s" % cmd + "\n" + output.decode("utf-8"))

    def write_logs(self, output: str):
        log_file = Path(self.get_log_path(), "log")
        with log_file.open("w") as file:
            file.write(output)
