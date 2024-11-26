from pathlib import Path
from typing import (
    Dict,
    List,
    Optional,
    Union,
)

import importlib_resources
import luigi
import netaddr
from docker.models.containers import Container
from docker.transport import unixconn

from exasol_integration_test_docker_environment.lib import PACKAGE_NAME
from exasol_integration_test_docker_environment.lib.base.docker_base_task import (
    DockerBaseTask,
)
from exasol_integration_test_docker_environment.lib.base.json_pickle_parameter import (
    JsonPickleParameter,
)
from exasol_integration_test_docker_environment.lib.data.container_info import (
    ContainerInfo,
)
from exasol_integration_test_docker_environment.lib.data.docker_network_info import (
    DockerNetworkInfo,
)
from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageInfo,
    ImageState,
)
from exasol_integration_test_docker_environment.lib.test_environment.analyze_test_container import (
    DockerTestContainerBuild,
)
from exasol_integration_test_docker_environment.lib.test_environment.docker_container_copy import (
    copy_script_to_container,
)
from exasol_integration_test_docker_environment.lib.test_environment.parameter.test_container_parameter import (
    TestContainerParameter,
)


class SpawnTestContainer(DockerBaseTask, TestContainerParameter):
    environment_name: str = luigi.Parameter()  # type: ignore
    test_container_name: str = luigi.Parameter()  # type: ignore
    network_info: DockerNetworkInfo = JsonPickleParameter(
        DockerNetworkInfo, significant=False
    )  # type: ignore
    ip_address_index_in_subnet: int = luigi.IntParameter(significant=False)  # type: ignore
    attempt: int = luigi.IntParameter(1)  # type: ignore
    reuse_test_container: bool = luigi.BoolParameter(False, significant=False)  # type: ignore
    no_test_container_cleanup_after_success: bool = luigi.BoolParameter(False, significant=False)  # type: ignore
    no_test_container_cleanup_after_failure: bool = luigi.BoolParameter(False, significant=False)  # type: ignore
    docker_runtime: Optional[str] = luigi.OptionalParameter(None, significant=False)  # type: ignore
    certificate_volume_name: Optional[str] = luigi.OptionalParameter(None, significant=False)  # type: ignore

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.ip_address_index_in_subnet < 0:
            raise Exception(
                "ip_address_index_in_subnet needs to be greater than 0 got %s"
                % self.ip_address_index_in_subnet
            )

    def register_required(self):
        self.test_container_image_future = self.register_dependency(
            self.create_child_task(
                task_class=DockerTestContainerBuild,
                test_container_content=self.test_container_content,
            )
        )

    def is_reuse_possible(self) -> bool:
        test_container_image_info: ImageInfo = self.get_values_from_futures(
            self.test_container_image_future
        )[
            "test-container"
        ]  # type: ignore
        test_container = None
        with self._get_docker_client() as docker_client:
            try:
                test_container = docker_client.containers.get(self.test_container_name)
            except Exception as e:
                pass
            ret_val: bool = bool(
                self.network_info.reused
                and self.reuse_test_container
                and test_container is not None
                and test_container_image_info.get_target_complete_name()
                in test_container.image.tags
                and test_container_image_info.image_state == ImageState.USED_LOCAL.name
            )

        return ret_val

    def run_task(self):
        subnet = netaddr.IPNetwork(self.network_info.subnet)
        ip_address = str(subnet[2 + self.ip_address_index_in_subnet])
        container_info = None

        if self.is_reuse_possible():
            container_info = self._try_to_reuse_test_container(
                ip_address, self.network_info
            )
        if container_info is None:
            container_info = self._create_test_container(ip_address, self.network_info)
        with self._get_docker_client() as docker_client:
            docker_client.containers.get(self.test_container_name)
        self._copy_runtime_targets()
        self.return_object(container_info)

    def _copy_runtime_targets(self):
        self.logger.info(
            "Copy runtime targets in test container %s.", self.test_container_name
        )
        with self._get_docker_client() as docker_client:
            test_container = docker_client.containers.get(self.test_container_name)
            for runtime_mapping in self.test_container_content.runtime_mappings:
                if runtime_mapping.deployment_target is not None:
                    self.logger.warning(
                        f"Copy runtime target {runtime_mapping.target} "
                        f"in test container {self.test_container_name}."
                    )
                    try:
                        test_container.exec_run(
                            cmd=f"rm -r {runtime_mapping.deployment_target}"
                        )
                    except:
                        pass
                    test_container.exec_run(
                        cmd=f"cp -r {runtime_mapping.target} {runtime_mapping.deployment_target}"
                    )

    def _try_to_reuse_test_container(
        self, ip_address: str, network_info: DockerNetworkInfo
    ) -> Optional[ContainerInfo]:
        self.logger.info("Try to reuse test container %s", self.test_container_name)
        container_info = None
        try:
            network_aliases = self._get_network_aliases()
            container_info = self.create_container_info(
                ip_address, network_aliases, network_info
            )
        except Exception as e:
            self.logger.warning(
                "Tried to reuse test container %s, but got Exeception %s. "
                "Fallback to create new database.",
                self.test_container_name,
                e,
            )
        return container_info

    def _create_test_container(
        self, ip_address, network_info: DockerNetworkInfo
    ) -> ContainerInfo:
        self._remove_container(self.test_container_name)
        self.logger.info(f"Creating new test container {self.test_container_name}")
        test_container_image_info = self.get_values_from_futures(
            self.test_container_image_future
        )["test-container"]

        volumes: Dict[Union[str, Path], Dict[str, str]] = dict()
        for runtime_mapping in self.test_container_content.runtime_mappings:
            volumes[runtime_mapping.source.absolute()] = {
                "bind": runtime_mapping.target,
                "mode": "rw",
            }
        if self.certificate_volume_name is not None:
            volumes[self.certificate_volume_name] = {
                "bind": "/certificates",
                "mode": "ro",
            }

        with self._get_docker_client() as docker_client:
            docker_unix_sockets = [
                i
                for i in docker_client.api.adapters.values()
                if isinstance(i, unixconn.UnixHTTPAdapter)
            ]
            if len(docker_unix_sockets) > 0:
                host_docker_socker_path = docker_unix_sockets[0].socket_path
                volumes[host_docker_socker_path] = {
                    "bind": "/var/run/docker.sock",
                    "mode": "rw",
                }
            test_container = docker_client.containers.create(
                image=test_container_image_info.get_target_complete_name(),
                name=self.test_container_name,
                network_mode=None,
                command="sleep infinity",
                detach=True,
                volumes=volumes,
                labels={
                    "test_environment_name": self.environment_name,
                    "container_type": "test_container",
                },
                runtime=self.docker_runtime,
            )
            docker_network = docker_client.networks.get(network_info.network_name)
            network_aliases = self._get_network_aliases()
            docker_network.connect(
                test_container, ipv4_address=ip_address, aliases=network_aliases
            )
            test_container.start()
            self.register_certificates(test_container)
            container_info = self.create_container_info(
                ip_address, network_aliases, network_info
            )
            return container_info

    def _get_network_aliases(self):
        network_aliases = ["test_container", self.test_container_name]
        return network_aliases

    def create_container_info(
        self,
        ip_address: str,
        network_aliases: List[str],
        network_info: DockerNetworkInfo,
    ) -> ContainerInfo:
        with self._get_docker_client() as docker_client:
            test_container = docker_client.containers.get(self.test_container_name)
            if test_container.status != "running":
                raise Exception(f"Container {self.test_container_name} not running")
            container_info = ContainerInfo(
                container_name=self.test_container_name,
                ip_address=ip_address,
                network_aliases=network_aliases,
                network_info=network_info,
            )
        return container_info

    def _get_export_directory(self):
        return self.get_values_from_future(self.export_directory_future)  # type: ignore

    def _remove_container(self, container_name: str):
        try:
            with self._get_docker_client() as docker_client:
                container = docker_client.containers.get(container_name)
                container.remove(force=True)
                self.logger.info(
                    f"Removed container: name: '{container_name}', id: '{container.short_id}'"
                )
        except Exception as e:
            pass

    def register_certificates(self, test_container: Container):
        if self.certificate_volume_name is not None:
            script_name = "install_root_certificate.sh"
            script = (
                importlib_resources.files(PACKAGE_NAME)
                / "certificate_resources"
                / script_name
            )
            script_location_in_container = f"scripts/{script_name}"
            copy_script_to_container(
                script.read_text(),
                script_location_in_container,
                test_container,
            )

            exit_code, output = test_container.exec_run(
                f"bash {script_location_in_container}"
            )
            if exit_code != 0:
                raise RuntimeError(
                    f"Error installing certificates:{output.decode('utf-8')}"
                )

    def cleanup_task(self, success: bool):
        if (success and not self.no_test_container_cleanup_after_success) or (
            not success and not self.no_test_container_cleanup_after_failure
        ):
            try:
                self.logger.info(f"Cleaning up container %s", self.test_container_name)
                self._remove_container(self.test_container_name)
            except Exception as e:
                self.logger.error(
                    f"Error during removing container %s: %s",
                    self.test_container_name,
                    e,
                )
