import pytest
from docker.errors import DockerException

from exasol_integration_test_docker_environment.lib.docker.images.create.utils.docker_registry_image_checker import (
    DockerRegistryImageChecker,
)


def test_pull_success():
    image = "index.docker.io/registry:latest"
    checker = DockerRegistryImageChecker()
    exists = checker.check(image=image)
    assert exists, f"Image {image} does not exist"


def test_pull_fail_with_DockerException():
    image = "index.docker.io/registry:abc"
    checker = DockerRegistryImageChecker()
    with pytest.raises(DockerException) as e:
        checker.check(image=image)
