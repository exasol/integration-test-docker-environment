import importlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

SPAWN_TEST_ENVIRONMENT = importlib.import_module(
    "exasol_integration_test_docker_environment.lib.api.spawn_test_environment"
)
SPAWN_TEST_ENVIRONMENT_WITH_TEST_CONTAINER = importlib.import_module(
    "exasol_integration_test_docker_environment.lib.api.spawn_test_environment_with_test_container"
)


def _environment_info(
    credentials_file: Path | None,
    with_test_container: bool = False,
):
    confd_info = (
        None
        if credentials_file is None
        else SimpleNamespace(credentials_file=str(credentials_file))
    )
    return SimpleNamespace(
        database_info=SimpleNamespace(
            confd_info=confd_info,
            container_info=SimpleNamespace(
                container_name="database", volume_name="database-volume"
            ),
        ),
        test_container_info=(
            SimpleNamespace(container_name="test-container")
            if with_test_container
            else None
        ),
        network_info=SimpleNamespace(network_name="network"),
    )


@pytest.mark.parametrize(
    "module,with_test_container",
    [
        (SPAWN_TEST_ENVIRONMENT, False),
        (SPAWN_TEST_ENVIRONMENT_WITH_TEST_CONTAINER, True),
    ],
)
def test_cleanup_removes_resources_and_confd_credentials(
    monkeypatch, tmp_path, module, with_test_container
):
    credentials_file = tmp_path / "confd_credentials.json"
    credentials_file.write_text("secret", encoding="utf-8")
    environment_info = _environment_info(credentials_file, with_test_container)
    remove_container = Mock()
    remove_volume = Mock()
    remove_network = Mock()
    monkeypatch.setattr(module, "remove_docker_container", remove_container)
    monkeypatch.setattr(module, "remove_docker_volumes", remove_volume)
    monkeypatch.setattr(module, "remove_docker_networks", remove_network)

    module._cleanup(environment_info)

    expected_containers = [["database"]]
    if with_test_container:
        expected_containers.insert(0, ["test-container"])
    assert [
        call.args[0] for call in remove_container.call_args_list
    ] == expected_containers
    remove_volume.assert_called_once_with(["database-volume"])
    remove_network.assert_called_once_with(["network"])
    assert not credentials_file.exists()


@pytest.mark.parametrize(
    "module,with_test_container",
    [
        (SPAWN_TEST_ENVIRONMENT, False),
        (SPAWN_TEST_ENVIRONMENT_WITH_TEST_CONTAINER, True),
    ],
)
def test_cleanup_removes_credentials_even_when_resource_cleanup_fails(
    monkeypatch, tmp_path, module, with_test_container
):
    credentials_file = tmp_path / "confd_credentials.json"
    credentials_file.write_text("secret", encoding="utf-8")
    environment_info = _environment_info(credentials_file, with_test_container)
    monkeypatch.setattr(module, "remove_docker_container", Mock())
    monkeypatch.setattr(module, "remove_docker_volumes", Mock())
    monkeypatch.setattr(
        module, "remove_docker_networks", Mock(side_effect=RuntimeError("failed"))
    )

    with pytest.raises(RuntimeError, match="failed"):
        module._cleanup(environment_info)

    assert not credentials_file.exists()


@pytest.mark.parametrize(
    "module,with_test_container",
    [
        (SPAWN_TEST_ENVIRONMENT, False),
        (SPAWN_TEST_ENVIRONMENT_WITH_TEST_CONTAINER, True),
    ],
)
def test_cleanup_supports_environments_without_confd_credentials(
    monkeypatch, module, with_test_container
):
    environment_info = _environment_info(None, with_test_container)
    monkeypatch.setattr(module, "remove_docker_container", Mock())
    monkeypatch.setattr(module, "remove_docker_volumes", Mock())
    monkeypatch.setattr(module, "remove_docker_networks", Mock())

    module._cleanup(environment_info)
