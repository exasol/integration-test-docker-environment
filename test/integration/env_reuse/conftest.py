from pathlib import Path
from uuid import uuid4

import pytest

from exasol_integration_test_docker_environment.lib.models.config.build_config import (
    set_build_config,
)
from exasol_integration_test_docker_environment.lib.models.config.docker_config import (
    set_docker_repository_config,
)
from exasol_integration_test_docker_environment.testing import luigi_utils
from test.integration.env_reuse.environment import ReusingTestEnv


def _setup_luigi_config(output_directory: Path, docker_repository_name: str):
    set_build_config(
        force_rebuild=False,
        force_pull=False,
        force_rebuild_from=(),
        log_build_context_content=False,
        output_directory=str(output_directory),
        cache_directory="",
        build_name="",
        temporary_base_directory="/tmp",
    )
    set_docker_repository_config(
        docker_password=None,
        docker_repository_name=docker_repository_name,
        docker_username=None,
        tag_prefix="",
        kind="target",
    )


@pytest.fixture
def reuse_environment_name(env_name: str) -> str:
    return f"{env_name}_{uuid4().hex[:8]}"


@pytest.fixture
def docker_repository(tmp_path, reuse_environment_name):
    _setup_luigi_config(
        output_directory=tmp_path / "output",
        docker_repository_name=reuse_environment_name,
    )
    luigi_utils.clean(reuse_environment_name)
    yield reuse_environment_name
    luigi_utils.clean(reuse_environment_name)


@pytest.fixture
def reusing_test_env(docker_repository, reuse_environment_name):
    environment = ReusingTestEnv(reuse_environment_name)
    try:
        yield environment
    finally:
        environment.cleanup()
