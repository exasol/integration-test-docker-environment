import shutil
import unittest

import luigi

import exasol_integration_test_docker_environment.certificate_resources.container
from exasol_integration_test_docker_environment.lib.api.common import (
    generate_root_task,
    set_docker_repository_config,
)
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.docker.images.clean.clean_images import (
    CleanImagesStartingWith,
)
from exasol_integration_test_docker_environment.lib.docker.images.utils import (
    find_images_by_tag,
)
from exasol_integration_test_docker_environment.lib.test_environment.create_certificates.analyze_certificate_container import (
    DockerCertificateContainerBuild,
)
from exasol_integration_test_docker_environment.lib.utils.resource_directory import (
    ResourceDirectory,
)


class DockerCertificateBuildTest(unittest.TestCase):

    def clean(self):
        task = generate_root_task(
            task_class=CleanImagesStartingWith,
            starts_with_pattern="exasol-certificate-docker-build",
        )
        success = luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
        task.cleanup(success)

    def setUp(self):
        self.clean()

    def tearDown(self):
        self.clean()

    def assert_image_exists(self, prefix):
        with ContextDockerClient() as docker_client:
            image_list = find_images_by_tag(
                docker_client, lambda x: x.startswith(prefix)
            )
            self.assertEqual(
                len(image_list), 1, f"Image with prefix {prefix} not found"
            )

    def test_build(self):
        try:
            set_docker_repository_config(
                docker_password=None,
                docker_repository_name="exasol-certificate-docker-build",
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
            self.assert_image_exists(
                "exasol-certificate-docker-build:certificate_resources"
            )
        finally:
            task.cleanup(success)


if __name__ == "__main__":
    unittest.main()
