from pathlib import Path
from unittest.mock import MagicMock

from docker.models.containers import ExecResult
from paramiko.ssh_exception import SSHException

from exasol_integration_test_docker_environment.lib.models.data.database_credentials import (
    DatabaseCredentials,
)
from exasol_integration_test_docker_environment.lib.test_environment.database_waiters.is_database_ready_thread import (
    IsDatabaseReadyThread,
)


def _thread(executor: MagicMock) -> IsDatabaseReadyThread:
    executor_factory = MagicMock()
    executor_factory.executor.return_value.__enter__.return_value = executor
    database_info = MagicMock()
    database_info.ports.database = 8563
    database_info.ports.bucketfs_http = 2580
    return IsDatabaseReadyThread(
        logger=MagicMock(),
        database_info=database_info,
        database_container=MagicMock(),
        database_credentials=DatabaseCredentials("sys", "password", "bucketfs"),
        docker_db_image_version="7.1.0",
        executor_factory=executor_factory,
    )


def test_retries_ssh_readiness_without_failing_database_startup(monkeypatch):
    executor = MagicMock()
    executor.prepare.side_effect = [SSHException("SSH banner not ready"), None]
    executor.exec.side_effect = [ExecResult(0, b""), ExecResult(0, b"")]
    thread = _thread(executor)
    sleep = MagicMock()
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.test_environment.database_waiters.is_database_ready_thread.find_exaplus",
        lambda *_: Path("/exa/bin/exaplus"),
    )
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.test_environment.database_waiters.is_database_ready_thread.time.sleep",
        sleep,
    )

    thread.run()

    assert thread.is_ready
    assert executor.prepare.call_count == 2
    assert executor.exec.call_count == 2


def test_stops_ssh_readiness_wait_when_database_waiter_stops_thread(monkeypatch):
    executor = MagicMock()
    executor.prepare.side_effect = SSHException("SSH banner not ready")
    thread = _thread(executor)

    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.test_environment.database_waiters.is_database_ready_thread.time.sleep",
        lambda _: thread.stop(),
    )

    thread.run()

    assert not thread.is_ready
    executor.exec.assert_not_called()


def test_stops_when_exaplus_cannot_be_found(monkeypatch):
    executor = MagicMock()
    thread = _thread(executor)
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.test_environment.database_waiters.is_database_ready_thread.find_exaplus",
        MagicMock(side_effect=RuntimeError("exaplus is unavailable")),
    )

    thread.run()

    assert thread.finish
    assert not thread.is_ready
    executor.exec.assert_not_called()


def test_stops_when_executor_context_cannot_be_opened():
    executor = MagicMock()
    thread = _thread(executor)
    thread.executor_factory.executor.side_effect = RuntimeError("cannot connect")

    thread.run()

    assert thread.finish
    assert not thread.is_ready
