import tempfile
import unittest
from pathlib import Path
from sys import stderr
from typing import List

import luigi
from exasol.bucketfs import Service, Bucket, as_string
from exasol_bucketfs_utils_python import list_files

from exasol_integration_test_docker_environment.lib.api.common import generate_root_task, run_task
from exasol_integration_test_docker_environment.lib.test_environment.database_setup.upload_file_to_db import \
    UploadFileToBucketFS, UploadResult
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing.api_test_environment import ApiTestEnvironment

BUCKET_NAME = "default"
PATH_IN_BUCKET = "upload_test"


def construct_upload_target(file_to_upload: str) -> str:
    return f"{BUCKET_NAME}/{PATH_IN_BUCKET}/{file_to_upload}"


class TestfileUpload(UploadFileToBucketFS):
    path = luigi.Parameter()
    file_to_upload = luigi.Parameter()  # type: str

    def get_log_file(self) -> str:
        return "/exa/logs/cored/*bucketfsd*"

    def get_pattern_to_wait_for(self) -> str:
        return f"{self.file_to_upload}.*linked"

    def get_file_to_upload(self) -> str:
        return f"{Path(str(self.path)) / str(self.file_to_upload)}"

    def get_upload_target(self) -> str:
        return construct_upload_target(self.file_to_upload)

    def get_sync_time_estimation(self) -> int:
        """Estimated time in seconds which the bucketfs needs to extract and sync a uploaded file"""
        return 10


class TestUpload(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}", file=stderr)
        cls.test_environment = ApiTestEnvironment(cls)
        cls.docker_environment_name = cls.__name__
        cls.environment = \
            cls.test_environment.spawn_docker_test_environment(name=cls.docker_environment_name)

    @classmethod
    def tearDownClass(cls):
        utils.close_environments(cls.environment, cls.test_environment)

    def _upload(self, temp_dir: str, file_to_upload: str, reuse: bool) -> UploadResult:
        task_creator = lambda: generate_root_task(task_class=TestfileUpload,
                                                  path=temp_dir,
                                                  file_to_upload=file_to_upload,
                                                  environment_name=self.environment.name,
                                                  test_environment_info=self.environment.environment_info,
                                                  bucketfs_write_password=self.environment.bucketfs_password,
                                                  reuse_uploaded=reuse)
        result = run_task(task_creator=task_creator, log_level="INFO")
        return result

    def _get_bucket(self) -> Bucket:
        db_info = self.environment.environment_info.database_info
        URL = f"http://{db_info.host}:{db_info.ports.bucketfs}"
        CREDENTAILS = {BUCKET_NAME: {"username": self.environment.bucketfs_username,
                                     "password": self.environment.bucketfs_password}}
        bucketfs = Service(URL, CREDENTAILS)
        return bucketfs.buckets[BUCKET_NAME]

    def _download_file(self, filename: str) -> str:
        file_content = as_string(self._get_bucket().download(f"{PATH_IN_BUCKET}/{filename}"))
        return file_content

    def _assert_file_upload(self, file_name: str,
                            upload_result: UploadResult,
                            expected_reuse: bool,
                            expected_content: str):
        files = self._get_bucket().files
        self.assertEqual(upload_result, UploadResult(
            upload_target=construct_upload_target(file_name),
            reused=expected_reuse
        ))
        self.assertIn(f"{PATH_IN_BUCKET}/{file_name}", list(files))
        content = self._download_file(file_name)
        self.assertEqual(content, expected_content)

    def _create_file_and_upload(self,
                                local_directory: str,
                                content: str,
                                upload_target: str,
                                reuse: bool) -> UploadResult:
        with open(f"{local_directory}/{upload_target}", "w") as f:
            f.write(content)
        return self._upload(local_directory, upload_target, reuse)

    def test_upload_without_reuse(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            file_one = "test1.txt"
            result_file_one = self._create_file_and_upload(
                local_directory=temp_directory,
                content=file_one,
                upload_target=file_one,
                reuse=False
            )
            file_two = "test2.txt"
            result_file_two = self._create_file_and_upload(
                local_directory=temp_directory,
                content=file_two,
                upload_target=file_two,
                reuse=False
            )
        self._assert_file_upload(file_name=file_one,
                                 upload_result=result_file_one,
                                 expected_reuse=False,
                                 expected_content=file_one)
        self._assert_file_upload(file_name=file_two,
                                 upload_result=result_file_two,
                                 expected_reuse=False,
                                 expected_content=file_two)

    def test_upload_with_reuse(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            file_reuse = "test_reuse.txt"
            result = self._create_file_and_upload(
                local_directory=temp_directory,
                content=file_reuse,
                upload_target=file_reuse,
                reuse=True
            )
        self._assert_file_upload(file_name=file_reuse,
                                 upload_result=result,
                                 expected_reuse=False,
                                 expected_content=file_reuse)

    def test_reupload_with_reuse(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            file_reupload_reuse = "test_reupload_reuse.txt"
            result = self._create_file_and_upload(
                local_directory=temp_directory,
                content=file_reupload_reuse,
                upload_target=file_reupload_reuse,
                reuse=True
            )
            self._assert_file_upload(file_name=file_reupload_reuse,
                                     upload_result=result,
                                     expected_reuse=False,
                                     expected_content=file_reupload_reuse)

            result = self._create_file_and_upload(
                local_directory=temp_directory,
                content=file_reupload_reuse,
                upload_target=file_reupload_reuse,
                reuse=True
            )
            self._assert_file_upload(file_name=file_reupload_reuse,
                                     upload_result=result,
                                     expected_reuse=True,
                                     expected_content=file_reupload_reuse)

    def test_reupload_without_reuse(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            file_reupload_no_reuse = "test_reupload_no_reuse.txt"
            result = self._create_file_and_upload(
                local_directory=temp_directory,
                content=file_reupload_no_reuse,
                upload_target=file_reupload_no_reuse,
                reuse=False
            )
            self._assert_file_upload(file_name=file_reupload_no_reuse,
                                     upload_result=result,
                                     expected_reuse=False,
                                     expected_content=file_reupload_no_reuse)

            expected_content_after_reupload = file_reupload_no_reuse + "2"
            result = self._create_file_and_upload(
                local_directory=temp_directory,
                content=expected_content_after_reupload,
                upload_target=file_reupload_no_reuse,
                reuse=False
            )
            self._assert_file_upload(file_name=file_reupload_no_reuse,
                                     upload_result=result,
                                     expected_reuse=False,
                                     expected_content=expected_content_after_reupload)


if __name__ == '__main__':
    unittest.main()
