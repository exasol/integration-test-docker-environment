from typing import Optional

from exasol_integration_test_docker_environment.lib.base.db_os_executor import (
    DbOsExecFactory,
    DockerClientFactory,
    DockerExecFactory,
    SshExecFactory,
)
from exasol_integration_test_docker_environment.lib.data.container_info import (
    ContainerInfo,
)
from exasol_integration_test_docker_environment.lib.data.database_info import (
    DatabaseInfo,
)
from exasol_integration_test_docker_environment.lib.data.docker_network_info import (
    DockerNetworkInfo,
)
from exasol_integration_test_docker_environment.lib.data.docker_volume_info import (
    DockerVolumeInfo,
)
from exasol_integration_test_docker_environment.lib.data.environment_type import (
    EnvironmentType,
)
from exasol_integration_test_docker_environment.lib.test_environment.abstract_spawn_test_environment import (
    AbstractSpawnTestEnvironment,
)
from exasol_integration_test_docker_environment.lib.test_environment.create_certificates.create_ssl_certificates_task import (
    CreateSSLCertificatesTask,
)
from exasol_integration_test_docker_environment.lib.test_environment.database_waiters.wait_for_test_docker_database import (
    WaitForTestDockerDatabase,
)
from exasol_integration_test_docker_environment.lib.test_environment.db_version import (
    db_version_supports_custom_certificates,
)
from exasol_integration_test_docker_environment.lib.test_environment.parameter.docker_db_test_environment_parameter import (
    DbOsAccess,
    DockerDBTestEnvironmentParameter,
)
from exasol_integration_test_docker_environment.lib.test_environment.prepare_network_for_test_environment import (
    PrepareDockerNetworkForTestEnvironment,
)
from exasol_integration_test_docker_environment.lib.test_environment.spawn_test_database import (
    SpawnTestDockerDatabase,
)


class SpawnTestEnvironmentWithDockerDB(
    AbstractSpawnTestEnvironment, DockerDBTestEnvironmentParameter
):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_container_name = f"""db_container_{self.environment_name}"""
        self.certificate_volume_name = f"""certificates_{self.environment_name}"""

    def get_environment_type(self):
        return EnvironmentType.docker_db

    def create_ssl_certificates(self):
        if not db_version_supports_custom_certificates(self.docker_db_image_version):
            raise ValueError(
                "Minimal supported Database with custom certificates is '7.0.6'"
            )
        return self.create_child_task_with_common_params(
            CreateSSLCertificatesTask,
            environment_name=self.environment_name,
            db_container_name=self.db_container_name,
            network_name=self.network_name,
            docker_runtime=self.docker_runtime,
            volume_name=self.certificate_volume_name,
            reuse=self.reuse_database or self.reuse_test_container,
            no_cleanup_after_success=self.no_database_cleanup_after_success
            or self.no_test_container_cleanup_after_success,
            no_cleanup_after_failure=self.no_database_cleanup_after_failure
            or self.no_test_container_cleanup_after_failure,
        )

    def create_network_task(self, attempt: int):
        return self.create_child_task_with_common_params(
            PrepareDockerNetworkForTestEnvironment,
            test_container_name=self.test_container_name,
            network_name=self.network_name,
            db_container_name=self.db_container_name,
            reuse=self.reuse_database or self.reuse_test_container,
            no_cleanup_after_success=self.no_database_cleanup_after_success
            or self.no_test_container_cleanup_after_success,
            no_cleanup_after_failure=self.no_database_cleanup_after_failure
            or self.no_test_container_cleanup_after_failure,
            attempt=attempt,
        )

    def _executor_factory(self, database_info: DatabaseInfo) -> DbOsExecFactory:
        if self.db_os_access == DbOsAccess.SSH:
            return SshExecFactory.from_database_info(database_info)
        client_factory = DockerClientFactory(timeout=100000)
        return DockerExecFactory(self.db_container_name, client_factory)

    def create_spawn_database_task(
        self,
        network_info: DockerNetworkInfo,
        certificate_volume_info: Optional[DockerVolumeInfo],
        attempt: int,
    ):
        def volume_name(info):
            return None if info is None else info.volume_name

        return self.create_child_task_with_common_params(
            SpawnTestDockerDatabase,
            db_container_name=self.db_container_name,
            network_info=network_info,
            certificate_volume_name=volume_name(certificate_volume_info),
            ip_address_index_in_subnet=0,
            attempt=attempt,
            additional_db_parameter=self.additional_db_parameter,
        )

    def create_wait_for_database_task(self, attempt: int, database_info: DatabaseInfo):
        return self.create_child_task_with_common_params(
            WaitForTestDockerDatabase,
            database_info=database_info,
            attempt=attempt,
            docker_db_image_version=self.docker_db_image_version,
            executor_factory=self._executor_factory(database_info),
        )
