import luigi

from exasol_integration_test_docker_environment.lib.base.docker_base_task import (
    DockerBaseTask,
)
from exasol_integration_test_docker_environment.lib.base.json_pickle_parameter import (
    JsonPickleParameter,
)
from exasol_integration_test_docker_environment.lib.data.database_credentials import (
    DatabaseCredentialsParameter,
)
from exasol_integration_test_docker_environment.lib.data.database_info import (
    DatabaseInfo,
)


class WaitForTestExternalDatabase(DockerBaseTask, DatabaseCredentialsParameter):
    environment_name: str = luigi.Parameter()  # type: ignore
    database_info: DatabaseInfo = JsonPickleParameter(DatabaseInfo, significant=False)  # type: ignore
    db_startup_timeout_in_seconds: int = luigi.IntParameter(1 * 60, significant=False)  # type: ignore
    attempt: int = luigi.IntParameter(1)  # type: ignore

    def run_task(self):
        # Since we can't assume that the test container exists, we cannot connect easily here
        # to the external database (correct way would be by using an SQL client).
        # For now, we simply assume that the external database is already ready and return just True.
        self.return_object(True)
