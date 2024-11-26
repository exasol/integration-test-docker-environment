import logging
from pathlib import (
    Path,
    PurePath,
)

import luigi

from exasol_integration_test_docker_environment.abstract_method_exception import (
    AbstractMethodException,
)
from exasol_integration_test_docker_environment.lib.base.docker_base_task import (
    DockerBaseTask,
)
from exasol_integration_test_docker_environment.lib.base.json_pickle_parameter import (
    JsonPickleParameter,
)
from exasol_integration_test_docker_environment.lib.data.database_credentials import (
    DatabaseCredentialsParameter,
)
from exasol_integration_test_docker_environment.lib.data.environment_info import (
    EnvironmentInfo,
)


class PopulateTestDataToDatabase(DockerBaseTask, DatabaseCredentialsParameter):
    logger = logging.getLogger("luigi-interface")

    environment_name: str = luigi.Parameter()  # type: ignore
    test_environment_info: EnvironmentInfo = JsonPickleParameter(
        EnvironmentInfo, significant=False
    )  # type: ignore

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._test_container_info = self.test_environment_info.test_container_info
        self._database_info = self.test_environment_info.database_info

    def run_task(self):
        self.logger.warning("Uploading data")
        username = self.db_user
        password = self.db_password
        data_path_within_test_container = self.get_data_path_within_test_container()
        data_file_within_data_path = self.get_data_file_within_data_path()
        with self._get_docker_client() as docker_client:
            test_container = docker_client.containers.get(
                self._test_container_info.container_name
            )
            cmd = (
                f"cd {data_path_within_test_container}; "
                f"$EXAPLUS -c '{self._database_info.host}:{self._database_info.ports.database}' "
                f"-x -u '{username}' -p '{password}' -f {data_file_within_data_path} "
                f"-jdbcparam 'validateservercertificate=0'"
            )

            bash_cmd = f"""bash -c "{cmd}" """
            exit_code, output = test_container.exec_run(cmd=bash_cmd)
        self.write_logs(output.decode("utf-8"))
        if exit_code != 0:
            raise Exception(
                "Failed to populate the database with data.\nLog: %s" % cmd
                + "\n"
                + output.decode("utf-8")
            )

    def write_logs(self, output: str):
        log_file = Path(self.get_log_path(), "log")
        with log_file.open("w") as file:
            file.write(output)

    def get_data_path_within_test_container(self) -> PurePath:
        raise AbstractMethodException()

    def get_data_file_within_data_path(self) -> PurePath:
        raise AbstractMethodException()
