import functools
import inspect
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
import shlex
from sys import stderr
from typing import List

from exasol_integration_test_docker_environment.lib.data.environment_info import EnvironmentInfo
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.docker.container.utils import remove_docker_container
from exasol_integration_test_docker_environment.lib.docker.volumes.utils import remove_docker_volumes
from exasol_integration_test_docker_environment.testing.docker_registry import default_docker_repository_name
from exasol_integration_test_docker_environment.testing.exaslct_docker_test_environment import \
    ExaslctDockerTestEnvironment
from exasol_integration_test_docker_environment.testing.spawned_test_environments import SpawnedTestEnvironments
from exasol_integration_test_docker_environment.testing.utils import find_free_ports, check_db_version_from_env


def _cleanup(env_name: str):
    remove_docker_container([f"test_container_{env_name}",
                             f"db_container_{env_name}"])
    remove_docker_volumes([f"db_container_{env_name}_volume"])


def get_class(test_object):
    if test_object is None:
        return None
    if not inspect.isclass(self.test_object):
        # test_object is an instance -> return its class
        return  self.test_object.__class__
    return self.test_object


class ExaslctTestEnvironment:

    def __init__(self, test_object, executable="./exaslct", clean_images_at_close=True, name=None):
        self.clean_images_at_close = clean_images_at_close
        self.executable = executable
        self.test_object = test_object
        self.test_class = get_class(test_object)
        self.flavor_path = self.get_test_flavor()
        self.name = name if name else self.test_class.__name__
        self._docker_repository_name = default_docker_repository_name(self.name)
        if "RUN_SLC_TESTS_WITHIN_CONTAINER" in os.environ:
            # We need to put the output directories into the workdir,
            # because only this is shared between the current container and
            # host. Only paths within this shared directory can be mounted
            # to docker container started by exaslct
            temp_dir_prefix_path = Path("./temp_outputs")
            temp_dir_prefix_path.mkdir(exist_ok=True)
            self.temp_dir = tempfile.mkdtemp(dir=temp_dir_prefix_path)
        else:
            self.temp_dir = tempfile.mkdtemp()
        self._update_attributes()

    def get_test_flavor(self):
        if self.test_class is None:
            return None
        source_file_of_test_object = inspect.getsourcefile(self.test_class)
        flavor_path = Path(os.path.realpath(source_file_of_test_object)).parent.joinpath(
            "resources/test-flavor")
        return flavor_path

    @property
    def repository_name(self):
        return self._docker_repository_name

    @repository_name.setter
    def repository_name(self, value):
        self._docker_repository_name = value
        self._update_attributes()

    def _update_attributes(self):
        self.flavor_path_argument = f"--flavor-path {self.get_test_flavor()}"
        repository_name = self.repository_name
        self.docker_repository_arguments = f"--source-docker-repository-name {repository_name} " \
                                           f"--target-docker-repository-name {repository_name}"
        self.clean_docker_repository_arguments = f"--docker-repository-name {repository_name}"
        self.output_directory_arguments = f"--output-directory {self.temp_dir}"
        self.task_dependencies_argument = " ".join([f"--task-dependencies-dot-file {self.name}.dot", ])

    def clean_images(self):
        self.run_command(f"{self.executable} clean-flavor-images", clean=True)

    def run_command(self, command: str,
                    use_output_directory: bool = True,
                    use_flavor_path: bool = True,
                    use_docker_repository: bool = True,
                    track_task_dependencies: bool = False,
                    clean: bool = False,
                    capture_output: bool = False):
        if use_output_directory:
            command = f"{command} {self.output_directory_arguments}"
        if track_task_dependencies:
            command = f"{command} {self.task_dependencies_argument}"
        if use_flavor_path:
            command = f"{command} {self.flavor_path_argument}"
        if use_docker_repository and not clean:
            command = f"{command} {self.docker_repository_arguments}"
        if use_docker_repository and clean:
            command = f"{command} {self.clean_docker_repository_arguments}"
        print(file=stderr)
        print(f"command: {command}", file=stderr)
        if capture_output:
            completed_process = subprocess.run(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        else:
            completed_process = subprocess.run(shlex.split(command))
        try:
            completed_process.check_returncode()
        except subprocess.CalledProcessError as e:
            if capture_output:
                print(e.stdout.decode("UTF-8"), file=stderr)
            raise e
        return completed_process

    def close(self):
        try:
            if self.clean_images_at_close:
                self.clean_images()
        except Exception as e:
            print(e, file=stderr)
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(e, file=stderr)

    def spawn_docker_test_environments(self, name: str, additional_parameter: List[str] = None) \
            -> SpawnedTestEnvironments:
        database_port, bucketfs_port = find_free_ports(2)
        on_host_parameter = ExaslctDockerTestEnvironment(
            name=self.name + "_" + name,
            database_host="localhost",
            db_username="sys",
            db_password="exasol",
            bucketfs_username="w",
            bucketfs_password="write",
            database_port=database_port,
            bucketfs_port=bucketfs_port)

        arguments = [
            f"--environment-name {on_host_parameter.name}",
            f"--database-port-forward {on_host_parameter.database_port}",
            f"--bucketfs-port-forward {on_host_parameter.bucketfs_port}",
        ]
        db_version = check_db_version_from_env()
        if db_version:
            arguments.append(f'--docker-db-image-version "{db_version}"')
        if additional_parameter:
            arguments += additional_parameter
        arguments = " ".join(arguments)

        command = f"{self.executable} spawn-test-environment {arguments}"
        completed_process = self.run_command(command, use_flavor_path=False, use_docker_repository=False,
                                             capture_output=True)
        on_host_parameter.completed_process = completed_process
        environment_info_json_path = Path(self.temp_dir,
                                          f"cache/environments/{on_host_parameter.name}/environment_info.json")
        if environment_info_json_path.exists():
            with environment_info_json_path.open() as f:
                environment_info = EnvironmentInfo.from_json(f.read())
                on_host_parameter.environment_info = environment_info
        on_host_parameter.clean_up = functools.partial(_cleanup, on_host_parameter.name)
        if "RUN_SLC_TESTS_WITHIN_CONTAINER" in os.environ:
            slc_test_run_parameter = ExaslctDockerTestEnvironment(
                name=on_host_parameter.name,
                database_host="localhost",
                db_username=on_host_parameter.db_username,
                db_password=on_host_parameter.db_password,
                bucketfs_username=on_host_parameter.bucketfs_username,
                bucketfs_password=on_host_parameter.bucketfs_password,
                database_port=8888,
                bucketfs_port=6583,
                environment_info=on_host_parameter.completed_process,
                completed_process=on_host_parameter.completed_process
            )

            with ContextDockerClient() as docker_client:
                db_container = docker_client.containers.get(f"db_container_{slc_test_run_parameter.name}")
                cloudbuild_network = docker_client.networks.get("cloudbuild")
                cloudbuild_network.connect(db_container)
                db_container.reload()
                slc_test_run_parameter.database_host = \
                    db_container.attrs["NetworkSettings"]["Networks"][cloudbuild_network.name]["IPAddress"]
                return SpawnedTestEnvironments(on_host_parameter, slc_test_run_parameter)
        else:
            return SpawnedTestEnvironments(on_host_parameter, None)

