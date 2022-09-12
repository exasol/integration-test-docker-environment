import inspect
import os
import shutil
import tempfile
from pathlib import Path
from sys import stderr
from typing import Dict, Any

from exasol_integration_test_docker_environment.lib.api import spawn_test_environment
from exasol_integration_test_docker_environment.lib.api import spawn_test_environment_with_test_container
from exasol_integration_test_docker_environment.lib.data.test_container_content_description import \
    TestContainerContentDescription
from exasol_integration_test_docker_environment.testing.docker_registry import default_docker_repository_name
from exasol_integration_test_docker_environment.testing.exaslct_docker_test_environment import \
    ExaslctDockerTestEnvironment
from exasol_integration_test_docker_environment.testing.utils import find_free_ports


class ApiTestEnvironment:

    def __init__(self, test_object):
        self.test_object = test_object
        if not inspect.isclass(self.test_object):
            self.test_class = self.test_object.__class__
        else:
            self.test_class = self.test_object
        self.flavor_path = self.get_test_flavor()
        self.name = self.test_class.__name__
        self.docker_repository_name = default_docker_repository_name(self.name)
        self.temp_dir = tempfile.mkdtemp()

    def get_test_flavor(self):
        source_file_of_test_object = inspect.getsourcefile(self.test_class)
        flavor_path = Path(os.path.realpath(source_file_of_test_object)).parent.joinpath(
            "resources/test-flavor")
        return flavor_path

    @property
    def output_dir(self):
        return self.temp_dir

    @property
    def task_dependency_dot_file(self):
        return f"{self.name}.dot"

    def close(self):
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(e, file=stderr)

    def _get_default_test_environment(self, name: str, database_port: int, bucketfs_port: int):
        return ExaslctDockerTestEnvironment(
            name=self.name + "_" + name,
            database_host="localhost",
            db_username="sys",
            db_password="exasol",
            bucketfs_username="w",
            bucketfs_password="write",
            database_port=database_port,
            bucketfs_port=bucketfs_port)

    def spawn_docker_test_environment_with_test_container(self, name: str,
                                                          test_container_content: TestContainerContentDescription,
                                                          additional_parameter: Dict[str, Any] = None) \
            -> ExaslctDockerTestEnvironment:
        if additional_parameter is None:
            additional_parameter = dict()
        database_port, bucketfs_port = find_free_ports(2)
        on_host_parameter = self._get_default_test_environment(name, database_port, bucketfs_port)
        docker_db_image_version = on_host_parameter.docker_db_image_version
        on_host_parameter.environment_info, on_host_parameter.clean_up = \
            spawn_test_environment_with_test_container(environment_name=on_host_parameter.name,
                                                       database_port_forward=on_host_parameter.database_port,
                                                       bucketfs_port_forward=on_host_parameter.bucketfs_port,
                                                       docker_db_image_version=docker_db_image_version,
                                                       test_container_content=test_container_content,
                                                       **additional_parameter)
        return on_host_parameter

    def spawn_docker_test_environment(self, name: str,
                                      additional_parameter: Dict[str, Any] = None) \
            -> ExaslctDockerTestEnvironment:
        if additional_parameter is None:
            additional_parameter = dict()
        database_port, bucketfs_port = find_free_ports(2)
        on_host_parameter = self._get_default_test_environment(name, database_port, bucketfs_port)
        on_host_parameter.environment_info, on_host_parameter.clean_up = \
            spawn_test_environment(environment_name=on_host_parameter.name,
                                   database_port_forward=on_host_parameter.database_port,
                                   bucketfs_port_forward=on_host_parameter.bucketfs_port,
                                   docker_db_image_version=on_host_parameter.docker_db_image_version,
                                   **additional_parameter)
        return on_host_parameter
