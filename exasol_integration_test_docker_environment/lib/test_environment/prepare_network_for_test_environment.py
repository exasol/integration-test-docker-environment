from typing import Optional

import docker
import luigi

from exasol_integration_test_docker_environment.lib.base.docker_base_task import (
    DockerBaseTask,
)
from exasol_integration_test_docker_environment.lib.data.docker_network_info import (
    DockerNetworkInfo,
)


class PrepareDockerNetworkForTestEnvironment(DockerBaseTask):
    environment_name: str = luigi.Parameter()  # type: ignore
    network_name: str = luigi.Parameter()  # type: ignore
    test_container_name: str = luigi.Parameter(significant=False)  # type: ignore
    db_container_name: Optional[str] = luigi.OptionalParameter(None, significant=False)  # type: ignore
    reuse: bool = luigi.BoolParameter(False, significant=False)  # type: ignore
    no_cleanup_after_success: bool = luigi.BoolParameter(False, significant=False)  # type: ignore
    no_cleanup_after_failure: bool = luigi.BoolParameter(False, significant=False)  # type: ignore
    attempt: int = luigi.IntParameter(-1)  # type: ignore

    def run_task(self):
        self.network_info = None
        if self.reuse:
            self.logger.info("Try to reuse network %s", self.network_name)
            try:
                self.network_info = self.get_network_info(reused=True)
            except Exception as e:
                self.logger.warning(
                    "Tried to reuse network %s, but got Exeception %s. "
                    "Fallback to create new network.",
                    self.network_name,
                    e,
                )
        if self.network_info is None:
            self.network_info = self.create_docker_network()
        self.return_object(self.network_info)

    def get_network_info(self, reused: bool):
        with self._get_docker_client() as docker_client:
            network_properties = docker_client.api.inspect_network(self.network_name)
            network_config = network_properties["IPAM"]["Config"][0]
            return DockerNetworkInfo(
                network_name=self.network_name,
                subnet=network_config["Subnet"],
                gateway=network_config["Gateway"],
                reused=reused,
            )

    def create_docker_network(self) -> DockerNetworkInfo:
        self.remove_container(self.test_container_name)
        if self.db_container_name is not None:
            self.remove_container(self.db_container_name)
        self.remove_network(self.network_name)
        with self._get_docker_client() as docker_client:
            network = docker_client.networks.create(
                name=self.network_name,
                driver="bridge",
            )
            network_info = self.get_network_info(reused=False)
            subnet = network_info.subnet
            gateway = network_info.gateway
            ipam_pool = docker.types.IPAMPool(subnet=subnet, gateway=gateway)
            ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
            self.remove_network(
                self.network_name
            )  # TODO race condition possible, add retry
            network = docker_client.networks.create(
                name=self.network_name, driver="bridge", ipam=ipam_config
            )
        return network_info

    def remove_network(self, network_name):
        try:
            with self._get_docker_client() as docker_client:
                docker_client.networks.get(network_name).remove()
                self.logger.info("Removed network %s", network_name)
        except docker.errors.NotFound:
            pass

    def remove_container(self, container_name: str):
        try:
            with self._get_docker_client() as docker_client:
                container = docker_client.containers.get(container_name)
                container.remove(force=True)
                self.logger.info("Removed container %s", container_name)
        except docker.errors.NotFound:
            pass

    def cleanup_task(self, success):
        if (success and not self.no_cleanup_after_success) or (
            not success and not self.no_cleanup_after_failure
        ):
            try:
                self.logger.info(f"Cleaning up container %s:", self.test_container_name)
                self.remove_container(self.test_container_name)
            except Exception as e:
                self.logger.error(
                    f"Error during removing container %s: %s:",
                    self.test_container_name,
                    e,
                )

            if self.db_container_name is not None:
                try:
                    self.logger.info(
                        f"Cleaning up container %s", self.db_container_name
                    )
                    self.remove_container(self.db_container_name)
                except Exception as e:
                    self.logger.error(
                        f"Error during removing container %s: %s: ",
                        self.db_container_name,
                        e,
                    )

            try:
                self.logger.info(f"Cleaning up dpcker network %s", self.network_name)
                self.remove_network(self.network_name)
            except Exception as e:
                self.logger.error(
                    f"Error during removing container %s: %s", self.network_name, e
                )
