from pathlib import Path

import luigi
from docker.models.containers import Container

# TODO add timeout, because sometimes the upload stucks
from exasol_integration_test_docker_environment.abstract_method_exception import AbstractMethodException
from exasol_integration_test_docker_environment.lib.base.docker_base_task import DockerBaseTask
from exasol_integration_test_docker_environment.lib.base.json_pickle_parameter import JsonPickleParameter
from exasol_integration_test_docker_environment.lib.base.still_running_logger import StillRunningLogger, \
    StillRunningLoggerThread
from exasol_integration_test_docker_environment.lib.data.environment_info import EnvironmentInfo
from exasol_integration_test_docker_environment.lib.test_environment.database_setup.docker_db_log_based_bucket_sync_checker import \
    DockerDBLogBasedBucketFSSyncChecker
from exasol_integration_test_docker_environment.lib.test_environment.database_setup.time_based_bucketfs_sync_waiter import \
    TimeBasedBucketFSSyncWaiter


class UploadFileToBucketFS(DockerBaseTask):
    environment_name = luigi.Parameter()
    test_environment_info = JsonPickleParameter(
        EnvironmentInfo, significant=False)  # type: EnvironmentInfo
    reuse_uploaded = luigi.BoolParameter(False, significant=False)
    bucketfs_write_password = luigi.Parameter(
        significant=False, visibility=luigi.parameter.ParameterVisibility.HIDDEN)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._test_container_info = self.test_environment_info.test_container_info
        self._database_info = self.test_environment_info.database_info

    def run_task(self):
        file_to_upload = self.get_file_to_upload()
        upload_target = self.get_upload_target()
        pattern_to_wait_for = self.get_pattern_to_wait_for()
        log_file = self.get_log_file()
        sync_time_estimation = self.get_sync_time_estimation()

        if self._database_info.container_info is not None:
            database_container = self._client.containers.get(
                self._database_info.container_info.container_name)
        else:
            database_container = None
        if not self.should_be_reused(upload_target):
            self.upload_and_wait(database_container,
                                 file_to_upload,
                                 upload_target,
                                 log_file,
                                 pattern_to_wait_for,
                                 sync_time_estimation)
        else:
            self.logger.warning("Reusing uploaded target %s instead of file %s",
                                upload_target, file_to_upload)
            self.write_logs("Reusing")

    def upload_and_wait(self, database_container,
                        file_to_upload: str, upload_target: str,
                        log_file: str, pattern_to_wait_for: str,
                        sync_time_estimation: int):
        still_running_logger = StillRunningLogger(self.logger,
                                                  "file upload of %s to %s"
                                                  % (file_to_upload, upload_target))
        thread = StillRunningLoggerThread(still_running_logger)
        thread.start()
        sync_checker = self.get_sync_checker(database_container, sync_time_estimation,
                                             log_file, pattern_to_wait_for)
        sync_checker.prepare_upload()
        output = self.upload_file(file_to_upload=file_to_upload, upload_target=upload_target)
        sync_checker.wait_for_bucketfs_sync()
        thread.stop()
        thread.join()
        self.write_logs(output)

    def get_sync_checker(self, database_container: Container,
                         sync_time_estimation: int,
                         log_file: str,
                         pattern_to_wait_for: str):
        if database_container is not None:
            return DockerDBLogBasedBucketFSSyncChecker(
                database_container=database_container,
                log_file_to_check=log_file,
                pattern_to_wait_for=pattern_to_wait_for,
                logger=self.logger,
                bucketfs_write_password=self.bucketfs_write_password
            )
        else:
            return TimeBasedBucketFSSyncWaiter(sync_time_estimation)

    def should_be_reused(self, upload_target: str):
        return self.reuse_uploaded and self.exist_file_in_bucketfs(upload_target)

    def exist_file_in_bucketfs(self, upload_target: str) -> bool:
        self.logger.info("Check if file %s exist in bucketfs", upload_target)
        command = self.generate_list_command(upload_target)
        exit_code, log_output = self.run_command("list", command)

        if exit_code != 0:
            self.write_logs(log_output)
            raise Exception("List files in bucketfs failed, got following output %s"
                            % (log_output))
        upload_target_in_bucket = "/".join(upload_target.split("/")[1:])
        if upload_target_in_bucket in log_output.splitlines():
            return True
        else:
            return False

    def generate_list_command(self, upload_target: str):
        bucket = upload_target.split("/")[0]
        url = "http://w:{password}@{host}:{port}/{bucket}".format(
            host=self._database_info.host, port=self._database_info.bucketfs_port,
            bucket=bucket, password=self.bucketfs_write_password)
        cmd = f"curl --silent --show-error --fail '{url}'"
        return cmd

    def upload_file(self, file_to_upload: str, upload_target: str):
        self.logger.info("upload file %s to %s",
                         file_to_upload, upload_target)
        exit_code, log_output = self.run_command("upload", "ls " + str(Path(file_to_upload).parent))
        command = self.generate_upload_command(file_to_upload, upload_target)
        exit_code, log_output = self.run_command("upload", command)
        if exit_code != 0:
            self.write_logs(log_output)
            raise Exception("Upload of %s failed, got following output %s"
                            % (file_to_upload, log_output))
        return log_output

    def generate_upload_command(self, file_to_upload, upload_target):
        url = "http://w:{password}@{host}:{port}/{target}".format(
            host=self._database_info.host, port=self._database_info.bucketfs_port,
            target=upload_target, password=self.bucketfs_write_password)
        cmd = f"curl --silent --show-error --fail -X PUT -T '{file_to_upload}' '{url}'"
        return cmd

    def run_command(self, command_type, cmd):
        test_container = self._client.containers.get(self._test_container_info.container_name)
        self.logger.info("start %s command %s", command_type, cmd)
        exit_code, output = test_container.exec_run(cmd=cmd)
        self.logger.info("finish %s command %s", command_type, cmd)
        log_output = cmd + "\n\n" + output.decode("utf-8")
        return exit_code, log_output

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
