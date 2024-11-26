import inspect
import os
import shutil
import tempfile
from pathlib import Path
from sys import stderr
from typing import (
    Any,
    Dict,
    Optional,
)

from exasol_integration_test_docker_environment.lib.api import (
    spawn_test_environment,
    spawn_test_environment_with_test_container,
)
from exasol_integration_test_docker_environment.lib.data.test_container_content_description import (
    TestContainerContentDescription,
)
from exasol_integration_test_docker_environment.lib.test_environment.ports import Ports
from exasol_integration_test_docker_environment.testing.docker_registry import (
    default_docker_repository_name,
)
from exasol_integration_test_docker_environment.testing.exaslct_docker_test_environment import (
    ExaslctDockerTestEnvironment,
)
from exasol_integration_test_docker_environment.testing.exaslct_test_environment import (
    get_class,
    get_test_flavor,
)


class ApiTestEnvironment:

    def __init__(self, test_object, name=None):
        self.test_object = test_object
        self.test_class = get_class(test_object)
        self.flavor_path = get_test_flavor(self.test_class)
        self.name = name if name else self.test_class.__name__
        self.docker_repository_name = default_docker_repository_name(self.name)
        self.temp_dir = tempfile.mkdtemp()

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

    def _get_default_test_environment(self, name: str, ports: Ports):
        return ExaslctDockerTestEnvironment(
            name=self.name + "_" + name,
            database_host="localhost",
            db_username="sys",
            db_password="exasol",
            bucketfs_username="w",
            bucketfs_password="write",
            ports=ports,
        )

    def spawn_docker_test_environment_with_test_container(
        self,
        name: str,
        test_container_content: TestContainerContentDescription,
        additional_parameter: Optional[Dict[str, Any]] = None,
    ) -> ExaslctDockerTestEnvironment:
        if additional_parameter is None:
            additional_parameter = dict()
        ports = Ports.random_free()
        on_host_parameter = self._get_default_test_environment(name, ports)
        docker_db_image_version = on_host_parameter.docker_db_image_version
        on_host_parameter.environment_info, on_host_parameter.clean_up = (
            spawn_test_environment_with_test_container(
                environment_name=on_host_parameter.name,
                database_port_forward=ports.database,
                bucketfs_port_forward=ports.bucketfs,
                ssh_port_forward=ports.ssh,
                docker_db_image_version=docker_db_image_version,
                test_container_content=test_container_content,
                **additional_parameter,
            )
        )
        return on_host_parameter

    def spawn_docker_test_environment(
        self,
        name: str,
        additional_parameter: Optional[Dict[str, Any]] = None,
    ) -> ExaslctDockerTestEnvironment:
        if additional_parameter is None:
            additional_parameter = dict()
        ports = Ports.random_free()
        on_host = self._get_default_test_environment(name, ports)
        on_host.environment_info, on_host.clean_up = spawn_test_environment(
            environment_name=on_host.name,
            database_port_forward=on_host.ports.database,
            bucketfs_port_forward=on_host.ports.bucketfs,
            ssh_port_forward=on_host.ports.ssh,
            docker_db_image_version=on_host.docker_db_image_version,
            **additional_parameter,
        )
        return on_host
