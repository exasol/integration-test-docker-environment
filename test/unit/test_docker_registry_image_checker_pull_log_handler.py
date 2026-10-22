"""Tests for Docker registry image-checker pull-log parsing."""

import json

from exasol_integration_test_docker_environment.lib.docker.images.create.utils.docker_registry_image_checker import (
    DockerRegistryImageCheckerPullLogHandler,
)


def test_pull_log_handler_accepts_existing_layer():
    log_line = json.dumps(
        {
            "status": "Already exists",
            "progressDetail": {},
            "id": "7e49dc6156b0",
        }
    )

    assert DockerRegistryImageCheckerPullLogHandler().handle_log_line(log_line)


def test_pull_log_handler_accepts_pulling_status():
    log_line = json.dumps({"status": "Pulling from library/registry"})

    assert DockerRegistryImageCheckerPullLogHandler().handle_log_line(log_line)
