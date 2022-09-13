import tempfile
import unittest
from pathlib import Path
from sys import stderr

import luigi
from exasol_bucketfs_utils_python import list_files, download
from exasol_bucketfs_utils_python.bucket_config import BucketConfig
from exasol_bucketfs_utils_python.bucketfs_config import BucketFSConfig
from exasol_bucketfs_utils_python.bucketfs_connection_config import BucketFSConnectionConfig

from exasol_integration_test_docker_environment.lib.api.common import generate_root_task
from exasol_integration_test_docker_environment.lib.test_environment.database_setup.upload_file_to_db import \
    UploadFileToBucketFS
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing.api_test_environment import ApiTestEnvironment

BUCKET_NAME = "default"
PATH_IN_BUCKET = "upload_test"


class TestfileUpload(UploadFileToBucketFS):
    path = luigi.Parameter()
    file_to_upload = luigi.Parameter()

    def get_log_file(self) -> str:
        return "/exa/logs/cored/*bucketfsd*"

    def get_pattern_to_wait_for(self) -> str:
        return f"{self.file_to_upload}.*linked"

    def get_file_to_upload(self) -> str:
        return f"{Path(str(self.path)) / str(self.file_to_upload)}"

    def get_upload_target(self) -> str:
        return f"{BUCKET_NAME}/{PATH_IN_BUCKET}/{self.file_to_upload}"

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

    def _upload(self, temp_dir: str, file_to_upload: str):
        task = generate_root_task(task_class=TestfileUpload,
                                  path=temp_dir,
                                  file_to_upload=file_to_upload,
                                  environment_name=self.environment.name,
                                  test_environment_info=self.environment.environment_info,
                                  bucketfs_write_password=self.environment.bucketfs_password
                                  )
        try:
            success = luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
            if not success:
                raise Exception("Task failed")
        except Exception as e:
            task.cleanup(False)
            raise RuntimeError("Error uploading test file.") from e

    def get_bucket_config(self):
        db_info = self.environment.environment_info.database_info
        connection_config = BucketFSConnectionConfig(
            host=db_info.host, port=int(db_info.bucketfs_port),
            user=self.environment.bucketfs_username, pwd=self.environment.bucketfs_password,
            is_https=False)
        bucketfs_config = BucketFSConfig(
            connection_config=connection_config,
            bucketfs_name="bfsdefault")

        bucket_config = BucketConfig(
            bucket_name=BUCKET_NAME,
            bucketfs_config=bucketfs_config)

        return bucket_config

    def download_file_and_read(self, output_path: Path, filename: str):
        local_output_file_path = output_path / filename
        download.download_from_bucketfs_to_file(
            bucket_config=self.get_bucket_config(),
            bucket_file_path=f"{PATH_IN_BUCKET}/{filename}",
            local_file_path=local_output_file_path)
        file_content = local_output_file_path.read_text()
        return file_content

    def test_upload(self):
        with tempfile.TemporaryDirectory() as d:
            file_one = "test1.txt"
            file_two = "test2.txt"
            with open(f"{d}/{file_one}", "w") as f:
                f.write(file_one)
            with open(f"{d}/{file_two}", "w") as f:
                f.write(file_two)

            self._upload(d, file_one)
            self._upload(d, file_two)

        bucket_config = self.get_bucket_config()
        files = list_files.list_files_in_bucketfs(bucket_config=bucket_config, bucket_file_path=PATH_IN_BUCKET)
        self.assertEquals(sorted(list(files)), [file_one, file_two])
        with tempfile.TemporaryDirectory() as d_target:
            p_target = Path(d_target)
            file_one_content = self.download_file_and_read(p_target, file_one)
            assert file_one_content == file_one
            file_two_content = self.download_file_and_read(p_target, file_two)
            assert file_two_content == file_two


if __name__ == '__main__':
    unittest.main()
