import os
import shutil
import tempfile
import unittest
from datetime import datetime

import docker
import luigi

from exasol_integration_test_docker_environment.cli.common import set_build_config, set_docker_repository_config
from exasol_integration_test_docker_environment.lib.base.docker_base_task import DockerBaseTask
from exasol_integration_test_docker_environment.lib.docker.images.clean.clean_images import CleanImagesStartingWith
from exasol_integration_test_docker_environment.lib.test_environment.prepare_network_for_test_environment import \
    PrepareDockerNetworkForTestEnvironment
from exasol_integration_test_docker_environment.lib.test_environment.spawn_test_container import SpawnTestContainer


class TestTask(DockerBaseTask):

    def register_required(self):
        docker_network_task = PrepareDockerNetworkForTestEnvironment(
            environment_name="test_environment_TestContainerReuseTest",
            network_name="docker_network_TestContainerReuseTest",
            test_container_name="test_container_TestContainerReuseTest",
            db_container_name="db_container_TestContainerReuseTest",
            reuse=False,
            no_cleanup_after_success=True,
            no_cleanup_after_failure=False,
            attempt=1
        )
        self.docker_network_future = self.register_dependency(docker_network_task)

    def run_task(self):
        test_container_task = \
            SpawnTestContainer(
                environment_name="test_environment_TestContainerReuseTest",
                test_container_name="test_container_TestContainerReuseTest",
                network_info=self.docker_network_future.get_output(),
                ip_address_index_in_subnet=2,
                attempt=1,
                reuse_test_container=True,
                no_test_container_cleanup_after_success=True,
                no_test_container_cleanup_after_failure=False
            )
        print("CWD",os.getcwd())
        test_container_future = yield from self.run_dependencies(test_container_task)


class TestContainerReuseTest(unittest.TestCase):

    def set_job_id(self, task_cls):
        strftime = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        job_id = f"{strftime}_{task_cls.__name__}"
        config = luigi.configuration.get_config()
        config.set('job_config', 'job_id', job_id)
        return job_id

    def clean(self):
        jobid = self.set_job_id(CleanImagesStartingWith)
        task = CleanImagesStartingWith(starts_with_pattern="", jobid=jobid)
        luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
        if task._get_tmp_path_for_job().exists():
            shutil.rmtree(str(task._get_tmp_path_for_job()))

    def setUp(self):
        self.client = docker.from_env()
        self.temp_directory = tempfile.mkdtemp()
        set_build_config(force_rebuild=False,
                         force_pull=False,
                         force_rebuild_from=tuple(),
                         log_build_context_content=False,
                         output_directory=self.temp_directory,
                         cache_directory="",
                         build_name="",
                         temporary_base_directory="/tmp"
                         )
        set_docker_repository_config(
            docker_password=None,
            docker_repository_name=self.__class__.__name__,
            docker_username=None,
            tag_prefix="",
            kind="source"
        )
        self.clean()

    def tearDown(self):
        self.clean()
        shutil.rmtree(self.temp_directory)
        self.client.close()

    def test_test_container_reuse(self):
        self.set_job_id(SpawnTestContainer)
        try:
            task = TestTask()
            luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
        finally:
            if task._get_tmp_path_for_job().exists():
                shutil.rmtree(str(task._get_tmp_path_for_job()))


if __name__ == '__main__':
    unittest.main()
