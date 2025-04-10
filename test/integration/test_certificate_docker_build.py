import luigi

import exasol_integration_test_docker_environment.certificate_resources.container
from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
)
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.docker.images.utils import (
    find_images_by_tag,
)
from exasol_integration_test_docker_environment.lib.models.config.docker_config import (
    set_docker_repository_config,
)
from exasol_integration_test_docker_environment.lib.test_environment.create_certificates.analyze_certificate_container import (
    DockerCertificateContainerBuild,
)
from exasol_integration_test_docker_environment.lib.utils.resource_directory import (
    ResourceDirectory,
)


def assert_image_exists(prefix):
    with ContextDockerClient() as docker_client:
        image_list = find_images_by_tag(docker_client, lambda x: x.startswith(prefix))
        assert len(image_list) == 1, f"Image with prefix {prefix} not found"


def test_build(luigi_output, api_isolation_module, tmpdir):
    try:
        set_docker_repository_config(
            docker_password=None,
            docker_repository_name=api_isolation_module.docker_repository_name,
            docker_username=None,
            tag_prefix="",
            kind="target",
        )

        with ResourceDirectory(
            exasol_integration_test_docker_environment.certificate_resources.container
        ) as d:
            task = generate_root_task(
                task_class=DockerCertificateContainerBuild,
                certificate_container_root_directory=d,
            )
            success = luigi.build(
                [task], workers=1, local_scheduler=True, log_level="INFO"
            )
        assert_image_exists(
            f"{api_isolation_module.docker_repository_name}:certificate_resources"
        )
    finally:
        task.cleanup(success)
