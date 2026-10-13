from pathlib import Path

import pytest

from noxconfig import Config


def _config(root_path: Path) -> Config:
    return Config(
        root_path=root_path,
        project_name="source",
        python_versions=("3.14",),
        add_to_excluded_python_paths=(),
    )


def test_integration_targets_group_confd_access_files(tmp_path):
    integration_root = tmp_path / "test" / "integration"
    for directory in ("base_task", "docker_runtime", "env_reuse", "ssh_access"):
        (integration_root / directory).mkdir(parents=True)
    confd_access = integration_root / "confd_access"
    confd_access.mkdir()
    for index in range(7):
        (confd_access / f"test_{index}.py").touch()

    targets = _config(tmp_path).integration_test_targets

    assert (
        "test/integration/confd_access/test_0.py,test/integration/confd_access/test_4.py"
        in targets
    )
    assert (
        "test/integration/confd_access/test_1.py,test/integration/confd_access/test_5.py"
        in targets
    )
    assert len([target for target in targets if "confd_access" in target]) == 4


def test_group_test_targets_distributes_files_round_robin(tmp_path):
    config = _config(tmp_path)

    assert config._group_test_targets(["first", "second", "third"], 2) == [
        "first,third",
        "second",
    ]


def test_ci_matrix_size_fails_fast_when_limit_is_exceeded():
    with pytest.raises(ValueError, match="would create 257 jobs"):
        Config._validate_ci_matrix_size("integration tests", 257)
