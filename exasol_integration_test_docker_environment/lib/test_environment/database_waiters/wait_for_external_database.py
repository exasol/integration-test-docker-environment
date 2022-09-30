import luigi

from exasol_integration_test_docker_environment.lib.base.docker_base_task import DockerBaseTask
from exasol_integration_test_docker_environment.lib.base.json_pickle_parameter import JsonPickleParameter
from exasol_integration_test_docker_environment.lib.data.database_credentials import DatabaseCredentialsParameter
from exasol_integration_test_docker_environment.lib.data.database_info import DatabaseInfo


class WaitForTestExternalDatabase(DockerBaseTask,
                                  DatabaseCredentialsParameter):
    environment_name = luigi.Parameter()
    database_info = JsonPickleParameter(DatabaseInfo, significant=False)  # type: DatabaseInfo
    db_startup_timeout_in_seconds = luigi.IntParameter(1 * 60, significant=False)
    attempt = luigi.IntParameter(1)

    def run_task(self):
        # Since we can't assume that the test container exists, we cannot connect easily here
        # to the external database (correct way would be by using an SQL client).
        # For now, we simply assume that the external database is already ready and return just True.
        self.return_object(True)
