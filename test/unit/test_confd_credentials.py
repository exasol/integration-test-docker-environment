import json
import stat
from types import SimpleNamespace
from typing import (
    Any,
    cast,
)
from unittest.mock import (
    MagicMock,
    Mock,
)

import pytest

from exasol_integration_test_docker_environment.lib.base.db_os_executor import (
    DockerExecFactory,
    SshExecFactory,
)
from exasol_integration_test_docker_environment.lib.models.data.confd_info import (
    ConfdInfo,
)
from exasol_integration_test_docker_environment.lib.test_environment.create_confd_credentials import (
    CreateConfdCredentials,
)
from exasol_integration_test_docker_environment.lib.test_environment.database_waiters.wait_for_test_docker_database import (
    WaitForTestDockerDatabase,
)
from exasol_integration_test_docker_environment.lib.test_environment.parameter.docker_db_test_environment_parameter import (
    DbOsAccess,
)
from exasol_integration_test_docker_environment.lib.test_environment.ports import (
    Ports,
)
from exasol_integration_test_docker_environment.lib.test_environment.spawn_test_environment_with_docker_db import (
    SpawnTestEnvironmentWithDockerDB,
)


def test_confd_credentials_are_not_serialized_or_rendered(tmp_path):
    password = "disposable-secret"
    credentials_file = tmp_path / "confd_credentials.json"
    credentials_file.write_text(
        json.dumps({"username": "itde_confd", "password": password}),
        encoding="utf-8",
    )
    credentials_file.chmod(0o600)
    info = ConfdInfo("itde_confd", str(credentials_file), "172.18.0.2")

    credentials = info.read_credentials()

    assert credentials.username == "itde_confd"
    assert credentials.password == password
    assert password not in info.to_json()
    assert password not in repr(info)
    assert password not in repr(credentials)


def test_confd_credentials_rejects_a_non_owner_only_file(tmp_path):
    credentials_file = tmp_path / "confd_credentials.json"
    credentials_file.write_text(
        json.dumps({"username": "itde_confd", "password": "secret"}),
        encoding="utf-8",
    )
    credentials_file.chmod(0o640)
    info = ConfdInfo("itde_confd", str(credentials_file), "172.18.0.2")

    with pytest.raises(PermissionError):
        info.read_credentials()


def test_create_user_passes_the_password_only_as_container_environment():
    task = object.__new__(CreateConfdCredentials)
    task._wait_for_readiness = Mock()

    task._create_user("disposable-secret")

    command, environment, failure_message = task._wait_for_readiness.call_args.args
    assert "disposable-secret" not in command
    assert environment == {"CONFD_PASSWORD": "disposable-secret"}
    assert failure_message == "Disposable ConfD user could not be created"
    assert command == (
        "confd_client -c user_create -A "
        '\'{"username":"itde_confd","userid":20001,'
        '"group":"exaadm","login_enabled":true,"password":"\''
        '"$CONFD_PASSWORD"'
        '\'","encode_passwd":true}\''
    )


def test_change_user_password_passes_the_password_only_as_container_environment():
    task = object.__new__(CreateConfdCredentials)
    task._wait_for_readiness = Mock()

    task._change_user_password("disposable-secret")

    command, environment, failure_message = task._wait_for_readiness.call_args.args
    assert "disposable-secret" not in command
    assert environment == {"CONFD_PASSWORD": "disposable-secret"}
    assert failure_message == "Disposable ConfD user password could not be changed"
    assert command == (
        "confd_client -c user_passwd -A "
        '\'{"username":"itde_confd","password":"\''
        '"$CONFD_PASSWORD"'
        '\'","encode_passwd":true}\''
    )


def test_confd_credentials_file_is_owner_only(tmp_path):
    task = object.__new__(CreateConfdCredentials)
    task.environment_name = "environment"
    task.get_cache_path = Mock(return_value=tmp_path)

    credentials_file = task._write_credentials_file("disposable-secret")

    assert stat.S_IMODE(credentials_file.stat().st_mode) == 0o600
    assert json.loads(credentials_file.read_text(encoding="utf-8"))["password"] == (
        "disposable-secret"
    )


def test_confd_readiness_retries_a_bounded_number_of_times(monkeypatch):
    task = object.__new__(CreateConfdCredentials)
    task._run_confd = Mock(side_effect=RuntimeError("not ready"))
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.test_environment.create_confd_credentials.time.sleep",
        Mock(),
    )

    with pytest.raises(RuntimeError) as error:
        task._wait_for_rest_readiness("disposable-secret")

    assert str(error.value) == "ConfD REST endpoint did not become ready"
    assert task._run_confd.call_count == 12
    for command, environment in (call.args for call in task._run_confd.call_args_list):
        assert "disposable-secret" not in command
        assert environment["CONFD_PASSWORD"] == "disposable-secret"


def test_confd_service_readiness_retries_without_credentials(monkeypatch):
    task = object.__new__(CreateConfdCredentials)
    task._run_confd = Mock(side_effect=[RuntimeError("not ready"), None])
    sleep = Mock()
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.test_environment.create_confd_credentials.time.sleep",
        sleep,
    )

    task._wait_for_service_readiness()

    assert task._run_confd.call_count == 2
    command, environment = task._run_confd.call_args.args
    assert environment == {}
    assert "CONFD_PASSWORD" not in command
    assert 'test "$status" = 401' in command
    sleep.assert_called_once_with(1)


def _task_for_run() -> CreateConfdCredentials:
    task = cast(Any, object.__new__(CreateConfdCredentials))
    task.environment_name = "environment"
    task.database_info = SimpleNamespace(
        reused=False,
        container_info=object(),
        forwarded_ports=Ports(8563, 2580, confd=8443),
        host="172.18.0.2",
    )
    task.port_bind_address = None
    task.executor_factory = MagicMock()
    task.return_object = Mock()
    return task


def test_run_task_provisions_credentials_after_service_readiness(monkeypatch, tmp_path):
    task = _task_for_run()
    task._wait_for_service_readiness = Mock()
    task._create_user = Mock()
    task._wait_for_rest_readiness = Mock()
    task._write_credentials_file = Mock(return_value=tmp_path / "credentials.json")
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.test_environment.create_confd_credentials.secrets.token_urlsafe",
        Mock(return_value="disposable-secret"),
    )

    task.run_task()

    task._wait_for_service_readiness.assert_called_once_with()
    task._create_user.assert_called_once_with("disposable-secret")
    task._wait_for_rest_readiness.assert_called_once_with("disposable-secret")
    info = task.return_object.call_args.args[0]
    assert info.endpoint == "https://127.0.0.1:8443/RPC2"
    assert info.tunnel_target_host == "172.18.0.2"


def test_run_task_omits_endpoint_without_a_forwarded_confd_port(monkeypatch, tmp_path):
    task = _task_for_run()
    task.database_info.forwarded_ports = None
    task._wait_for_service_readiness = Mock()
    task._create_user = Mock()
    task._wait_for_rest_readiness = Mock()
    task._write_credentials_file = Mock(return_value=tmp_path / "credentials.json")
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.test_environment.create_confd_credentials.secrets.token_urlsafe",
        Mock(return_value="disposable-secret"),
    )

    task.run_task()

    assert task.return_object.call_args.args[0].endpoint is None


def test_run_task_rolls_back_only_a_created_user(monkeypatch):
    task = _task_for_run()
    task._wait_for_service_readiness = Mock()
    task._create_user = Mock()
    task._wait_for_rest_readiness = Mock(side_effect=RuntimeError("not ready"))
    task._delete_user = Mock()
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.test_environment.create_confd_credentials.secrets.token_urlsafe",
        Mock(return_value="disposable-secret"),
    )

    with pytest.raises(RuntimeError) as error:
        task.run_task()

    assert str(error.value) == "not ready"
    task._delete_user.assert_called_once_with()


def test_run_task_does_not_roll_back_when_user_creation_fails(monkeypatch):
    task = _task_for_run()
    task._wait_for_service_readiness = Mock()
    task._create_user = Mock(side_effect=RuntimeError("creation failed"))
    task._delete_user = Mock()
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.test_environment.create_confd_credentials.secrets.token_urlsafe",
        Mock(return_value="disposable-secret"),
    )

    with pytest.raises(RuntimeError) as error:
        task.run_task()

    assert str(error.value) == "creation failed"
    task._delete_user.assert_not_called()


def test_run_task_does_not_roll_back_when_service_is_not_ready():
    task = _task_for_run()
    task._wait_for_service_readiness = Mock(side_effect=RuntimeError("not ready"))
    task._create_user = Mock()
    task._delete_user = Mock()

    with pytest.raises(RuntimeError) as error:
        task.run_task()

    assert str(error.value) == "not ready"
    task._create_user.assert_not_called()
    task._delete_user.assert_not_called()


def test_run_task_returns_retained_credentials_for_a_reused_database(tmp_path):
    task = _task_for_run()
    task.database_info.reused = True
    task.get_cache_path = Mock(return_value=tmp_path)
    credentials_file = task._write_credentials_file("disposable-secret")
    task._wait_for_service_readiness = Mock()
    task._create_user = Mock()

    task.run_task()

    info = task.return_object.call_args.args[0]
    assert info.credentials_file == str(credentials_file)
    assert info.read_credentials().password == "disposable-secret"
    task._wait_for_service_readiness.assert_not_called()
    task._create_user.assert_not_called()


def test_run_task_repairs_reuse_when_credentials_file_is_missing(monkeypatch, tmp_path):
    task = _task_for_run()
    task.database_info.reused = True
    task.get_cache_path = Mock(return_value=tmp_path)
    task._change_user_password = Mock()
    task._create_user = Mock()
    task._wait_for_rest_readiness = Mock()
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.test_environment.create_confd_credentials.secrets.token_urlsafe",
        Mock(return_value="replacement-secret"),
    )

    task.run_task()

    task._change_user_password.assert_called_once_with("replacement-secret")
    task._create_user.assert_not_called()
    task._wait_for_rest_readiness.assert_called_once_with("replacement-secret")
    credentials_file = task._credentials_file_path()
    assert task.return_object.call_args.args[0].credentials_file == str(
        credentials_file
    )
    assert task.return_object.call_args.args[0].read_credentials().password == (
        "replacement-secret"
    )


def test_run_task_creates_missing_confd_account_while_repairing_credentials(
    monkeypatch, tmp_path
):
    task = _task_for_run()
    task.database_info.reused = True
    task.get_cache_path = Mock(return_value=tmp_path)
    task._change_user_password = Mock(side_effect=RuntimeError("user does not exist"))
    task._create_user = Mock()
    task._wait_for_rest_readiness = Mock()
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.test_environment.create_confd_credentials.secrets.token_urlsafe",
        Mock(return_value="replacement-secret"),
    )

    task.run_task()

    task._create_user.assert_called_once_with("replacement-secret")
    task._wait_for_rest_readiness.assert_called_once_with("replacement-secret")


def test_run_task_fails_without_writing_credentials_when_repair_is_impossible(
    monkeypatch, tmp_path
):
    task = _task_for_run()
    task.database_info.reused = True
    task.get_cache_path = Mock(return_value=tmp_path)
    task._change_user_password = Mock(side_effect=RuntimeError("ConfD unavailable"))
    task._create_user = Mock(side_effect=RuntimeError("ConfD unavailable"))
    task._wait_for_rest_readiness = Mock()
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.test_environment.create_confd_credentials.secrets.token_urlsafe",
        Mock(return_value="replacement-secret"),
    )

    with pytest.raises(RuntimeError, match="Cannot repair ConfD credentials"):
        task.run_task()

    assert not task._credentials_file_path().exists()
    task._wait_for_rest_readiness.assert_not_called()
    task.return_object.assert_not_called()


def test_run_task_rejects_reuse_for_a_different_confd_account(tmp_path):
    task = _task_for_run()
    task.database_info.reused = True
    task.get_cache_path = Mock(return_value=tmp_path)
    credentials_file = task._credentials_file_path()
    credentials_file.parent.mkdir(parents=True)
    credentials_file.write_text(
        json.dumps({"username": "different-user", "password": "secret"}),
        encoding="utf-8",
    )
    credentials_file.chmod(0o600)

    with pytest.raises(RuntimeError, match="different ConfD account"):
        task.run_task()


def test_docker_database_spawn_passes_its_executor_to_confd_credentials_task():
    task = object.__new__(SpawnTestEnvironmentWithDockerDB)
    task.create_confd_user = True
    task.environment_name = "environment"
    task.port_bind_address = "127.0.0.1"
    task._executor_factory = Mock(return_value="executor-factory")
    task.create_child_task_with_common_params = Mock(return_value="confd-task")
    database_info = Mock()

    result = task.create_confd_credentials_task(database_info)

    assert result == "confd-task"
    task.create_child_task_with_common_params.assert_called_once_with(
        CreateConfdCredentials,
        environment_name="environment",
        database_info=database_info,
        executor_factory="executor-factory",
        port_bind_address="127.0.0.1",
    )


def test_docker_database_spawn_skips_confd_credentials_without_opt_in():
    task = object.__new__(SpawnTestEnvironmentWithDockerDB)
    task.create_confd_user = False

    assert task.create_confd_credentials_task(Mock()) is None


def test_docker_database_readiness_uses_a_short_docker_timeout():
    task = object.__new__(SpawnTestEnvironmentWithDockerDB)
    task.db_os_access = DbOsAccess.DOCKER_EXEC
    task.db_container_name = "database"

    factory = task._readiness_executor_factory(Mock())

    assert isinstance(factory, DockerExecFactory)
    assert factory._container_name == "database"
    assert factory._client_factory._timeout == 30


def test_docker_database_readiness_uses_ssh_when_configured(monkeypatch):
    task = object.__new__(SpawnTestEnvironmentWithDockerDB)
    task.db_os_access = DbOsAccess.SSH
    database_info = Mock()
    factory = Mock()
    ssh_factory = Mock(return_value=factory)
    monkeypatch.setattr(SshExecFactory, "from_database_info", ssh_factory)

    assert task._readiness_executor_factory(database_info) is factory
    ssh_factory.assert_called_once_with(database_info)


def test_docker_database_wait_task_uses_the_readiness_executor():
    task = object.__new__(SpawnTestEnvironmentWithDockerDB)
    task.docker_db_image_version = "2026.1.0"
    task._readiness_executor_factory = Mock(return_value="readiness-executor")
    task.create_child_task_with_common_params = Mock(return_value="wait-task")
    database_info = Mock()

    assert task.create_wait_for_database_task(2, database_info) == "wait-task"
    task.create_child_task_with_common_params.assert_called_once_with(
        WaitForTestDockerDatabase,
        database_info=database_info,
        attempt=2,
        docker_db_image_version="2026.1.0",
        executor_factory="readiness-executor",
    )


def test_run_confd_uses_the_configured_executor_without_logging_output():
    task = object.__new__(CreateConfdCredentials)
    task.database_info = SimpleNamespace(container_info=None, host="172.18.0.2")
    executor = MagicMock()
    executor.exec.return_value = SimpleNamespace(exit_code=0)
    task.executor_factory = MagicMock()
    task.executor_factory.executor.return_value.__enter__.return_value = executor

    task._run_confd("command", {"CONFD_PASSWORD": "disposable-secret"})

    command, environment = executor.exec.call_args.args
    assert command.startswith("/bin/sh -c ")
    assert "COS_DIRECTORY" in command
    assert command.endswith(" command'")
    assert "disposable-secret" not in command
    assert environment == {
        "CONFD_HOST": "172.18.0.2",
        "HOSTNAME": "localhost",
        "CONFD_PASSWORD": "disposable-secret",
    }
    task.executor_factory.executor.assert_called_once_with()


def test_run_confd_raises_a_sanitized_error_for_a_failed_command():
    task = object.__new__(CreateConfdCredentials)
    task.database_info = SimpleNamespace(container_info=None, host="172.18.0.2")
    executor = MagicMock()
    executor.exec.return_value = SimpleNamespace(
        exit_code=1, output=b"The password is disposable-secret"
    )
    task.executor_factory = MagicMock()
    task.executor_factory.executor.return_value.__enter__.return_value = executor

    with pytest.raises(RuntimeError) as error:
        task._run_confd("command", {"CONFD_PASSWORD": "disposable-secret"})

    assert (
        str(error.value)
        == "Disposable ConfD user operation failed: The password is <redacted>"
    )
    assert "disposable-secret" not in str(error.value)


def test_delete_user_suppresses_a_sanitized_cleanup_failure():
    task = object.__new__(CreateConfdCredentials)
    task._run_confd = Mock(side_effect=RuntimeError("failure"))
    task.logger = Mock()

    task._delete_user()

    task.logger.warning.assert_called_once_with(
        "Unable to remove the disposable ConfD user"
    )


def test_write_credentials_removes_the_temporary_file_after_a_failure(
    monkeypatch, tmp_path
):
    task = object.__new__(CreateConfdCredentials)
    task.environment_name = "environment"
    task.get_cache_path = Mock(return_value=tmp_path)
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.test_environment.create_confd_credentials.json.dump",
        Mock(side_effect=OSError("write failed")),
    )

    with pytest.raises(OSError) as error:
        task._write_credentials_file("disposable-secret")

    assert str(error.value) == "write failed"
    assert not (
        tmp_path / "environments/environment/.confd_credentials.json.tmp"
    ).exists()


def test_failed_task_cleanup_removes_the_credentials_file(tmp_path):
    task = object.__new__(CreateConfdCredentials)
    task.environment_name = "environment"
    task.get_cache_path = Mock(return_value=tmp_path)
    credentials_file = task._write_credentials_file("disposable-secret")

    task.cleanup_task(success=False)

    assert not credentials_file.exists()


def test_successful_task_cleanup_preserves_the_credentials_file(tmp_path):
    task = object.__new__(CreateConfdCredentials)
    task.environment_name = "environment"
    task.get_cache_path = Mock(return_value=tmp_path)
    credentials_file = task._write_credentials_file("disposable-secret")

    task.cleanup_task(success=True)

    assert credentials_file.exists()


def test_readiness_returns_without_running_when_attempts_are_disabled(monkeypatch):
    task = object.__new__(CreateConfdCredentials)
    task._run_confd = Mock()
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.test_environment.create_confd_credentials.CONFD_READINESS_ATTEMPTS",
        0,
    )

    task._wait_for_readiness("command", None, "failure")

    task._run_confd.assert_not_called()
