import luigi
import os
import pytest

from typing import List, Optional

from exasol_integration_test_docker_environment \
    .testing.api_test_environment import ApiTestEnvironment
from dataclasses import dataclass
from exasol.bucketfs import Service, Bucket, as_string
from exasol_integration_test_docker_environment \
    .lib.test_environment.database_setup.upload_file_to_db \
    import (
        UploadFileToBucketFS,
        UploadResult,
    )
from exasol_integration_test_docker_environment.lib.api.common import (
    generate_root_task,
    run_task,
)
from exasol_integration_test_docker_environment \
    .lib.data.environment_info import EnvironmentInfo
from exasol_integration_test_docker_environment \
    .lib.data.database_info import DatabaseInfo
from exasol_integration_test_docker_environment \
    .lib.test_environment.parameter \
    .docker_db_test_environment_parameter import DbOsAccess
from exasol_integration_test_docker_environment \
    .lib.base.db_os_executor import (
        DbOsExecFactory,
        DockerExecFactory,
        SshExecFactory,
    )
from test.integration.helpers import get_executor_factory

BUCKET_NAME = "default"


def bucketfs_path(path: str, relative: bool = False) -> str:
    parent = "upload_test"
    suffix = f"{parent}/{path}"
    if relative:
        return suffix
    return f"{BUCKET_NAME}/{suffix}"


class ArgumentError(Exception):
    """Invalid arguments to BucketFsAccess.upload()"""


class BucketFsAccess:
    # TODO: eitde/lib/test_environment/database_setup/upload_file_to_db.py
    # at exasol_bucketfs_utils_python import list_files, upload
    # reports BucketFsDeprecationWarning:
    # This API is deprecated and will be dropped in the future,
    # please use the new API in the `exasol.bucketfs` package.
    class FileUploadTask(UploadFileToBucketFS):
        local_path = luigi.Parameter()
        target = luigi.Parameter()

        def get_log_file(self) -> str:
            return "/exa/logs/cored/*bucketfsd*"

        def get_pattern_to_wait_for(self) -> str:
            filename = os.path.basename(self.local_path)
            return f"{filename}.*linked"

        def get_file_to_upload(self) -> str:
            return str(self.local_path)

        def get_upload_target(self) -> str:
            return self.target

        def get_sync_time_estimation(self) -> int:
            """Estimated time in seconds which the bucketfs needs to extract and sync a uploaded file"""
            return 10

    def __init__(self, environment: ApiTestEnvironment, executor_factory: DbOsExecFactory):
        self.environment = environment
        self.executor_factory = executor_factory

    def _get_bucket(self) -> Bucket:
        db_info = self.environment.environment_info.database_info
        url = f"http://{db_info.host}:{db_info.ports.bucketfs}"
        credentials = { BUCKET_NAME: {
                "username": self.environment.bucketfs_username,
                "password": self.environment.bucketfs_password
        } }
        bucketfs = Service(url, credentials)
        return bucketfs.buckets[BUCKET_NAME]

    def list(self) -> List[str]:
        return self._get_bucket().files

    def upload(self,
               local_path: str,
               relative: Optional[str] = None,
               target: Optional[str] = None,
               reuse: bool = False) -> UploadResult:
        if not (relative or target):
            raise ArgumentError("Either relative or target must be specified.")
        if relative:
            local_path = f"{local_path}/{relative}"
        target = bucketfs_path(target or relative)
        task_creator = lambda: generate_root_task(
            task_class=self.FileUploadTask,
            local_path=local_path,
            target=target,
            environment_name=self.environment.name,
            test_environment_info=self.environment.environment_info,
            bucketfs_write_password=self.environment.bucketfs_password,
            reuse_uploaded=reuse,
            executor_factory=self.executor_factory,
        )
        result = run_task(task_creator=task_creator, log_level="INFO")
        return result

    def download(self, relative: str) -> str:
        path = bucketfs_path(path=relative, relative=True)
        return as_string(self._get_bucket().download(path))


class UploadValidator:
    def __init__(self, tmp_path: str, bucketfs: BucketFsAccess, reuse: bool):
        self.tmp_path = tmp_path
        self.bucketfs = bucketfs
        self.reuse = reuse
        self.filename = None
        self.actual_result = None

    def upload(self, filename: str, content: str):
        with open(f"{self.tmp_path}/{filename}", "w") as f:
            f.write(content)
        self.filename = filename
        self.actual_result = self.bucketfs.upload(
            self.tmp_path,
            relative=filename,
            reuse=self.reuse,
        )
        return self

    def validate(self, expected_content: str, expected_reuse: bool):
        expected_result = UploadResult(
            upload_target=bucketfs_path(self.filename),
            reused=expected_reuse,
        )
        assert self.actual_result == expected_result
        assert bucketfs_path(self.filename, relative=True) in self.bucketfs.list()
        assert expected_content == self.bucketfs.download(self.filename)


@pytest.mark.parametrize("db_os_access", [DbOsAccess.DOCKER_EXEC, DbOsAccess.SSH])
def test_upload_without_reuse(api_database, tmp_path, db_os_access):
    with api_database() as db:
        dbinfo = db.environment_info.database_info
        executor_factory = get_executor_factory(dbinfo, db_os_access)
        bucketfs = BucketFsAccess(db, executor_factory)
        filename = "sample-file.txt"
        validator = UploadValidator(tmp_path, bucketfs, reuse=False)
        validator.upload(filename, "old content") \
                 .validate("old content", expected_reuse=False)
        validator.upload(filename, "new content") \
                 .validate("new content", expected_reuse=False)


def test_upload_with_reuse(api_database, tmp_path):
    with api_database() as db:
        dbinfo = db.environment_info.database_info
        executor_factory = _executor_factory(dbinfo)
        bucketfs = BucketFsAccess(db, executor_factory)
        filename = "sample-file.txt"
        validator = UploadValidator(tmp_path, bucketfs, reuse=True)
        validator.upload(filename, "old content") \
                 .validate("old content", expected_reuse=False)
        validator.upload(filename, "new content") \
                 .validate("old content", expected_reuse=True)
