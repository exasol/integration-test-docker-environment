from __future__ import annotations

from pathlib import Path

from exasol.toolbox.config import BaseConfig
from pydantic import (
    BaseModel,
    computed_field,
)


class TestRunnersConfig(BaseModel):
    default_runner: str
    test_runners: list[str]


class Config(BaseConfig):
    @computed_field  # type: ignore[misc]
    @property
    def source_code_path(self) -> Path:
        """
        Path to the source code of the project.

        In the ITDE, this needs to be overridden due to a custom directory setup.
        This will be addressed in:
            https://github.com/exasol/integration-test-docker-environment/issues/569
        """
        return self.root_path / self.project_name

    test_runners_config: TestRunnersConfig


PROJECT_CONFIG = Config(
    root_path=Path(__file__).parent,
    project_name="exasol_integration_test_docker_environment",
    python_versions=("3.10", "3.11", "3.12", "3.13"),
    add_to_excluded_python_paths=("resources",),
    test_runners_config=TestRunnersConfig(
        default_runner="ubuntu-24.04",
        test_runners=[
            "ubuntu-24.04"
        ],  # TODO https://github.com/exasol/integration-tasks/issues/815
    ),
)
