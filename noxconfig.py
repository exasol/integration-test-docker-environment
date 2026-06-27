from __future__ import annotations

import re
from pathlib import Path

from exasol.toolbox.config import BaseConfig
from packaging.version import Version
from pydantic import computed_field

from exasol_integration_test_docker_environment.cli.options.test_environment_options import (
    LATEST_DB_VERSION,
)


class Config(BaseConfig):
    _INTEGRATION_TEST_DIRS = ("base_task", "docker_runtime")
    _MINIMAL_INTEGRATION_TEST_TARGETS = (
        "test/integration/base_task",
        "test/integration/test_api_logging.py",
        "test/integration/test_api_test_environment.py",
        "test/integration/test_cli_environment_bin_docker_exec.py",
        "test/integration/test_cli_environment_bin_docker_exec_certificates.py",
        "test/integration/test_cli_environment_bin_ssh.py",
        "test/integration/test_cli_environment_bin_ssh_certificates.py",
        "test/integration/test_cli_environment_cli_docker_exec.py",
        "test/integration/test_cli_environment_cli_docker_exec_certificates.py",
        "test/integration/test_cli_environment_cli_ssh.py",
        "test/integration/test_cli_environment_cli_ssh_certificates.py",
        "test/integration/test_cli_environment_bin_container_started.py",
        "test/integration/test_cli_environment_cli_container_started.py",
        "test/integration/test_db_container_log_thread.py",
    )

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

    @computed_field  # type: ignore[misc]
    @property
    def db_versions(self) -> list[str]:
        """
        Return all Exasol DB versions supported by the ITDE.

        The list is derived from the available docker-db templates and normalizes
        the latest template version to the synthetic `default` entry used by the
        test workflows.
        """
        template_path = self.root_path / "docker_db_config_template"
        db_versions = [
            str(path.name) for path in template_path.iterdir() if path.is_dir()
        ]
        return Config._normalize_default_version(db_versions)

    @computed_field  # type: ignore[misc]
    @property
    def db_versions_gpu_only(self) -> list[str]:
        """
        Return the Exasol DB versions supported by the GPU test workflows.

        This mirrors the current GPU-specific filtering logic and normalizes the
        latest template version to the synthetic `default` entry.
        """
        template_path = self.root_path / "docker_db_config_template"
        db_versions = [
            str(path.name) for path in template_path.iterdir() if path.is_dir()
        ]
        db_versions = [
            db_version
            for db_version in db_versions
            if Version(db_version) >= Version("2025.1.8")
        ]
        return Config._normalize_default_version(db_versions)

    @computed_field  # type: ignore[misc]
    @property
    def integration_test_targets(self) -> list[str]:
        """
        Return dynamic non-GPU integration test targets for CI matrix generation.
        """
        return self._discover_integration_test_targets()

    @computed_field  # type: ignore[misc]
    @property
    def minimal_integration_test_targets(self) -> list[str]:
        """
        Return the minimal non-GPU integration test targets for CI matrix generation.
        """
        valid_targets = set(self._discover_integration_test_targets())
        return sorted(
            target
            for target in self._MINIMAL_INTEGRATION_TEST_TARGETS
            if target in valid_targets
        )

    @computed_field  # type: ignore[misc]
    @property
    def slow_python_test_matrix(self) -> list[dict[str, str | bool]]:
        """
        Return the expanded matrix rows for the slow Python-version workflow.

        Coverage is enabled only for Python 3.10 rows, and every row includes the
        precomputed artifact name the workflow should use when coverage is collected.
        """
        rows: list[dict[str, str | bool]] = []
        for python_version in self.python_versions:
            for test_target in self.integration_test_targets:
                rows.append(
                    {
                        "python_versions": python_version,
                        "integration_test_targets": test_target,
                        "collect_coverage": python_version == "3.10",
                        "coverage_artifact_name": (
                            f"coverage-python{python_version}-slow-"
                            f"{self._sanitize_artifact_name(test_target)}"
                        ),
                    }
                )
        return rows

    def _discover_integration_test_targets(self) -> list[str]:
        test_root = self.root_path / "test" / "integration"
        targets = [
            str((test_root / directory).relative_to(self.root_path))
            for directory in self._INTEGRATION_TEST_DIRS
        ]
        targets.extend(
            str(path.relative_to(self.root_path))
            for path in sorted(test_root.glob("test_*.py"))
            if path.name != "test_gpu.py"
        )
        return sorted(targets)

    @staticmethod
    def _normalize_default_version(db_versions: list[str]) -> list[str]:
        normalized_db_versions = [
            db_version for db_version in db_versions if db_version != LATEST_DB_VERSION
        ]
        normalized_db_versions.append("default")
        return normalized_db_versions

    @staticmethod
    def _sanitize_artifact_name(target: str) -> str:
        sanitized = re.sub(r"[/.]+", "-", target)
        return sanitized.strip("-")


PROJECT_CONFIG = Config(
    root_path=Path(__file__).parent,
    project_name="exasol_integration_test_docker_environment",
    python_versions=("3.10", "3.11", "3.12", "3.13", "3.14"),
    add_to_excluded_python_paths=("resources",),
)
