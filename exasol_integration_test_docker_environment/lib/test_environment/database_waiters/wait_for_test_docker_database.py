import gzip
import pathlib
import time
from datetime import (
    datetime,
    timedelta,
)

import luigi
from docker.models.containers import Container

from exasol_integration_test_docker_environment.lib.base.db_os_executor import (
    DbOsExecFactory,
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
from exasol_integration_test_docker_environment.lib.data.database_info import (
    DatabaseInfo,
)
from exasol_integration_test_docker_environment.lib.test_environment.database_waiters.db_container_log_thread import (
    DBContainerLogThread,
)
from exasol_integration_test_docker_environment.lib.test_environment.database_waiters.is_database_ready_thread import (
    IsDatabaseReadyThread,
)


class WaitForTestDockerDatabase(DockerBaseTask, DatabaseCredentialsParameter):
    environment_name: str = luigi.Parameter()  # type: ignore
    database_info: DatabaseInfo = JsonPickleParameter(DatabaseInfo, significant=False)  # type: ignore
    db_startup_timeout_in_seconds: int = luigi.IntParameter(10 * 60, significant=False)  # type: ignore
    attempt: int = luigi.IntParameter(1)  # type: ignore
    docker_db_image_version: str = luigi.Parameter()  # type: ignore
    executor_factory: DbOsExecFactory = JsonPickleParameter(DbOsExecFactory, significant=False)  # type: ignore

    def run_task(self):
        with self._get_docker_client() as docker_client:
            db_container_name = self.database_info.container_info.container_name
            db_container = docker_client.containers.get(db_container_name)
            is_database_ready = self.wait_for_database_startup(db_container)
            after_startup_db_log_file = self.get_log_path().joinpath(
                "after_startup_db_log.tar.gz"
            )
            self.save_db_log_files_as_gzip_tar(after_startup_db_log_file, db_container)
            self.return_object(is_database_ready)

    def wait_for_database_startup(self, db_container: Container):
        container_log_thread, is_database_ready_thread = self.start_wait_threads(
            db_container
        )
        is_database_ready = self.wait_for_threads(
            container_log_thread, is_database_ready_thread
        )
        self.join_threads(container_log_thread, is_database_ready_thread)
        return is_database_ready

    def start_wait_threads(self, db_container: Container):
        startup_log_file = self.get_log_path().joinpath("startup.log")
        container_log_thread = DBContainerLogThread(
            db_container,
            self.logger,
            startup_log_file,
            "Database Startup %s" % db_container.name,
        )
        container_log_thread.start()
        is_database_ready_thread = IsDatabaseReadyThread(
            self.logger,
            self.database_info,
            db_container,
            self.get_database_credentials(),
            self.docker_db_image_version,
            self.executor_factory,
        )
        is_database_ready_thread.start()
        return container_log_thread, is_database_ready_thread

    def join_threads(
        self,
        container_log_thread: DBContainerLogThread,
        is_database_ready_thread: IsDatabaseReadyThread,
    ):
        container_log_thread.stop()
        is_database_ready_thread.stop()
        container_log_thread.join()
        is_database_ready_thread.join()

    def wait_for_threads(
        self,
        container_log_thread: DBContainerLogThread,
        is_database_ready_thread: IsDatabaseReadyThread,
    ):
        is_database_ready = False
        reason = None
        start_time = datetime.now()
        while True:
            if container_log_thread.error_message != None:
                is_database_ready = False
                reason = "error message in container log"
                break
            if is_database_ready_thread.finish and is_database_ready_thread.is_ready:
                is_database_ready = True
                break
            elif is_database_ready_thread.finish:
                reason = "error in is_database_ready_thread"
                break
            if self.timeout_occured(start_time):
                reason = (
                    f"timeout after after {self.db_startup_timeout_in_seconds} seconds"
                )
                is_database_ready = False
                break
            time.sleep(1)
        if not is_database_ready:
            self.log_database_not_ready(
                container_log_thread, is_database_ready_thread, reason
            )
        container_log_thread.stop()
        is_database_ready_thread.stop()
        return is_database_ready

    def log_database_not_ready(
        self,
        container_log_thread: DBContainerLogThread,
        is_database_ready_thread: IsDatabaseReadyThread,
        reason,
    ):
        container_log = "\n".join(container_log_thread.complete_log)
        log_information = f"""
========== IsDatabaseReadyThread output db connection: ============
{is_database_ready_thread.output_db_connection}
========== IsDatabaseReadyThread output bucketfs connection: ============
{is_database_ready_thread.output_bucketfs_connection}
========== Container-Log: ============
{container_log}
"""
        self.logger.warning(
            'Database startup failed for following reason "%s", here some debug information \n%s',
            reason,
            log_information,
        )

    def timeout_occured(self, start_time):
        timeout = timedelta(seconds=self.db_startup_timeout_in_seconds)
        return datetime.now() - start_time > timeout

    def save_db_log_files_as_gzip_tar(
        self, path: pathlib.Path, database_container: Container
    ):
        stream, stat = database_container.get_archive("/exa/logs")
        with gzip.open(path, "wb") as file:
            for chunk in stream:
                file.write(chunk)

    def write_output(self, is_database_ready: bool):
        with self.output().open("w") as file:
            file.write(str(is_database_ready))
