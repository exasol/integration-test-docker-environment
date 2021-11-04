import os
import shutil
import tempfile
import unittest
from pathlib import Path

import docker
import luigi

from exasol_integration_test_docker_environment.test.utils import process_spawn_utils
from exasol_integration_test_docker_environment.cli.common import set_build_config, set_docker_repository_config
from exasol_integration_test_docker_environment.lib.base.docker_base_task import DockerBaseTask
from exasol_integration_test_docker_environment.lib.data.container_info import ContainerInfo
from exasol_integration_test_docker_environment.lib.test_environment.prepare_network_for_test_environment import \
    PrepareDockerNetworkForTestEnvironment
from exasol_integration_test_docker_environment.lib.test_environment.spawn_test_container import SpawnTestContainer
from exasol_integration_test_docker_environment.test.utils import luigi_utils


class TestTask(DockerBaseTask):
    reuse = luigi.BoolParameter()
    attempt = luigi.IntParameter()

    def run_task(self):
        docker_network_task_1 = PrepareDockerNetworkForTestEnvironment(
            environment_name="test_environment_TestContainerReuseTest",
            network_name="docker_network_TestContainerReuseTest",
            test_container_name="test_container_TestContainerReuseTest",
            db_container_name="db_container_TestContainerReuseTest",
            reuse=self.reuse,
            no_cleanup_after_success=True,
            no_cleanup_after_failure=False,
            attempt=self.attempt
        )
        self.docker_network_future_1 = yield from self.run_dependencies(docker_network_task_1)

        test_container_task_1 = \
            SpawnTestContainer(
                environment_name="test_environment_TestContainerReuseTest",
                test_container_name="test_container_TestContainerReuseTest",
                network_info=self.docker_network_future_1.get_output(),
                ip_address_index_in_subnet=2,
                attempt=self.attempt,
                reuse_test_container=self.reuse,
                no_test_container_cleanup_after_success=True,
                no_test_container_cleanup_after_failure=False
            )
        test_container_future_1 = yield from self.run_dependencies(test_container_task_1)
        container_info = test_container_future_1.get_output()  # type: ContainerInfo
        container = self._client.containers.get(container_info.container_name)

        self.return_object({"container_id": container.image.id, "image_id": container.image.id})


class TestContainerReuseTest(unittest.TestCase):

    def setUp(self):
        self.client = docker.from_env()
        resource_directory = Path(Path(__file__).parent, "resources/test_test_container_reuse")
        print("resource_directory content", list(Path(resource_directory).iterdir()))
        self.temp_directory = tempfile.mkdtemp()
        self.working_directory = shutil.copytree(resource_directory,
                                                 Path(self.temp_directory, "test_test_container_reuse"))
        print("working_directory",self.working_directory)
        self.old_working_directory = os.getcwd()
        os.chdir(self.working_directory)
        print("working_directory content",list(Path(self.working_directory).iterdir()))
        self.docker_repository_name = self.__class__.__name__.lower()
        print("docker_repository_name",self.docker_repository_name)
        luigi_utils.clean(self.docker_repository_name)

    def tearDown(self):
        os.chdir(self.old_working_directory)
        luigi_utils.clean(self.docker_repository_name)
        shutil.rmtree(self.temp_directory)
        self.client.close()

    def setup_luigi_config(self):
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
            docker_repository_name=self.docker_repository_name,
            docker_username=None,
            tag_prefix="",
            kind="target"
        )

    def run1(self):
        self.setup_luigi_config()
        luigi_utils.set_job_id(SpawnTestContainer)
        task = TestTask(reuse=False, attempt=1)
        try:
            success = luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
            if success:
                result = task.get_return_object()
                task.cleanup(True)
                return result
            else:
                task.cleanup(False)
                Exception("Task failed")
        except Exception as e:
            task.cleanup(False)

    def run2(self):
        self.setup_luigi_config()
        luigi_utils.set_job_id(SpawnTestContainer)
        task = TestTask(reuse=True, attempt=2)
        try:
            success = luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")

            if success:
                result = task.get_return_object()
                return result
            else:
                raise Exception("Task failed")
        finally:
            task.cleanup(False)

    def test_test_container_no_reuse_after_change(self):
        p1 = process_spawn_utils.run_in_process(self.run1)
        dockerfile = Path(self.working_directory, "tests/Dockerfile")
        with dockerfile.open("a") as f:
            f.write("\n#Test\n")
        p2 = process_spawn_utils.run_in_process(self.run2)
        print(p1)
        print(p2)
        assert p1 != p2

    def test_test_container_reuse(self):
        p1 = process_spawn_utils.run_in_process(self.run1)
        p2 = process_spawn_utils.run_in_process(self.run2)
        print(p1)
        print(p2)
        assert p1 == p2


if __name__ == '__main__':
    unittest.main()
