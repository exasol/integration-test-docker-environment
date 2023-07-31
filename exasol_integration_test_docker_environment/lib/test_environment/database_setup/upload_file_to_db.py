import dataclasses
from pathlib import Path
from typing import Tuple

import luigi
from docker.models.containers import Container
from exasol_bucketfs_utils_python import list_files, upload
from exasol_bucketfs_utils_python.bucket_config import BucketConfig
from exasol_bucketfs_utils_python.bucketfs_config import BucketFSConfig
from exasol_bucketfs_utils_python.bucketfs_connection_config import BucketFSConnectionConfig

# TODO add timeout, because sometimes the upload stucks
from exasol_integration_test_docker_environment.abstract_method_exception import AbstractMethodException
from exasol_integration_test_docker_environment.lib.base.docker_base_task import DockerBaseTask
from exasol_integration_test_docker_environment.lib.base.json_pickle_parameter import JsonPickleParameter
from exasol_integration_test_docker_environment.lib.base.still_running_logger import StillRunningLogger, \
    StillRunningLoggerThread
from exasol_integration_test_docker_environment.lib.data.environment_info \
    import EnvironmentInfo
from exasol_integration_test_docker_environment \
    .lib.test_environment.database_setup.docker_db_log_based_bucket_sync_checker \
    import DockerDBLogBasedBucketFSSyncChecker
from exasol_integration_test_docker_environment \
    .lib.test_environment.database_setup.time_based_bucketfs_sync_waiter \
    import TimeBasedBucketFSSyncWaiter
from exasol_integration_test_docker_environment \
    .lib.base.db_os_executor import (
        DbOsExecutor,
        DbOsExecFactory,
    )


@dataclasses.dataclass
class UploadResult:
    upload_target: str
    reused: bool


class UploadFileToBucketFS(DockerBaseTask):
    environment_name = luigi.Parameter()
    test_environment_info = JsonPickleParameter(
        EnvironmentInfo, significant=False)  # type: EnvironmentInfo
    reuse_uploaded = luigi.BoolParameter(False, significant=False)
    bucketfs_write_password = luigi.Parameter(
        significant=False, visibility=luigi.parameter.ParameterVisibility.HIDDEN)
    executor_factory=JsonPickleParameter(DbOsExecFactory, significant=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._database_info = self.test_environment_info.database_info

    def run_task(self):
        file_to_upload = self.get_file_to_upload()
        upload_target = self.get_upload_target()
        pattern_to_wait_for = self.get_pattern_to_wait_for()
        log_file = self.get_log_file()
        sync_time_estimation = self.get_sync_time_estimation()

        with self._get_docker_client() as docker_client:
            if self._database_info.container_info is not None:
                database_container = docker_client.containers.get(
                    self._database_info.container_info.container_name)
            else:
                database_container = None
            if not self.should_be_reused(upload_target):
                with self.executor_factory.executor() as executor:
                    executor.prepare()
                    self.upload_and_wait(
                        database_container,
                        file_to_upload,
                        upload_target,
                        log_file,
                        pattern_to_wait_for,
                        sync_time_estimation,
                        db_os_executor=executor,
                    )
                    self.return_object(UploadResult(
                        upload_target=upload_target,
                        reused=False
                    ))
            else:
                self.logger.warning("Reusing uploaded target %s instead of file %s",
                                    upload_target, file_to_upload)
                self.write_logs("Reusing")
                self.return_object(UploadResult(
                    upload_target=upload_target,
                    reused=True
                ))

    def upload_and_wait(
            self,
            database_container,
            file_to_upload: str,
            upload_target: str,
            log_file: str,
            pattern_to_wait_for: str,
            sync_time_estimation: int,
            db_os_executor: DbOsExecutor,
    ):
        still_running_logger = StillRunningLogger(
            self.logger,
            f"file upload of {file_to_upload} to {upload_target}",
        )
        thread = StillRunningLoggerThread(still_running_logger)
        thread.start()
        sync_checker = self.get_sync_checker(
            database_container,
            sync_time_estimation,
            log_file,
            pattern_to_wait_for,
            db_os_executor=db_os_executor,
        )
        sync_checker.prepare_upload()
        try:
            output = self.upload_file(
                file_to_upload=file_to_upload,
                upload_target=upload_target,
            )
            sync_checker.wait_for_bucketfs_sync()
            self.write_logs(output)
        finally:
            thread.stop()
            thread.join()

    def get_sync_checker(
            self,
            database_container: Container,
            sync_time_estimation: int,
            log_file: str,
            pattern_to_wait_for: str,
            db_os_executor: DbOsExecutor,
    ):
        if database_container is not None:
            return DockerDBLogBasedBucketFSSyncChecker(
                database_container=database_container,
                log_file_to_check=log_file,
                pattern_to_wait_for=pattern_to_wait_for,
                logger=self.logger,
                bucketfs_write_password=str(self.bucketfs_write_password),
                executor=db_os_executor,
            )
        else:
            return TimeBasedBucketFSSyncWaiter(sync_time_estimation)

    def should_be_reused(self, upload_target: str):
        return self.reuse_uploaded and self.exist_file_in_bucketfs(upload_target)

    @staticmethod
    def split_upload_target(upload_target: str) -> Tuple[str, str, str]:
        upload_parts = upload_target.split("/")
        bucket_name = upload_parts[0]
        path_in_bucket = "/".join(upload_parts[1:-1])
        file_in_bucket = upload_parts[-1]
        return bucket_name, path_in_bucket, file_in_bucket

    def exist_file_in_bucketfs(self, upload_target: str) -> bool:
        self.logger.info("Check if file %s exist in bucketfs", upload_target)
        bucket_name, path_in_bucket, file_in_bucket = self.split_upload_target(upload_target)

        bucket_config = self.generate_bucket_config(bucket_name)
        try:
            files = list_files.list_files_in_bucketfs(
                bucket_config=bucket_config,
                bucket_file_path=path_in_bucket)
            return file_in_bucket in files
        except FileNotFoundError as ex:
            return False

    def generate_bucket_config(self, bucket_name: str) -> BucketConfig:
        connection_config = BucketFSConnectionConfig(
            host=self._database_info.host, port=int(self._database_info.ports.bucketfs),
            user="w", pwd=str(self.bucketfs_write_password),
            is_https=False)
        bucketfs_config = BucketFSConfig(
            connection_config=connection_config,
            bucketfs_name="bfsdefault")
        bucket_config = BucketConfig(
            bucket_name=bucket_name,
            bucketfs_config=bucketfs_config)
        return bucket_config

    def upload_file(self, file_to_upload: str, upload_target: str):
        self.logger.info("upload file %s to %s",
                         file_to_upload, upload_target)
        bucket_name, path_in_bucket, file_in_bucket = self.split_upload_target(upload_target)
        bucket_config = self.generate_bucket_config(bucket_name)
        upload.upload_file_to_bucketfs(
            bucket_config=bucket_config,
            bucket_file_path=f"{path_in_bucket}/{file_in_bucket}",
            local_file_path=Path(file_to_upload)
        )
        return f"File '{file_to_upload}' to '{upload_target}'"

    def write_logs(self, output):
        log_file = Path(self.get_log_path(), "log")
        with log_file.open("w") as file:
            file.write(output)

    def get_log_file(self) -> str:
        raise AbstractMethodException()

    def get_pattern_to_wait_for(self) -> str:
        raise AbstractMethodException()

    def get_file_to_upload(self) -> str:
        raise AbstractMethodException()

    def get_upload_target(self) -> str:
        raise AbstractMethodException()

    def get_sync_time_estimation(self) -> int:
        """Estimated time in seconds which the bucketfs needs to extract and sync a uploaded file"""
        raise AbstractMethodException()
