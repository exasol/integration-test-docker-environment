import json
import os
import secrets
import time
from pathlib import Path

import luigi

from exasol_integration_test_docker_environment.lib.base.docker_base_task import (
    DockerBaseTask,
)
from exasol_integration_test_docker_environment.lib.base.json_pickle_parameter import (
    JsonPickleParameter,
)
from exasol_integration_test_docker_environment.lib.models.data.confd_info import (
    ConfdInfo,
)
from exasol_integration_test_docker_environment.lib.models.data.database_info import (
    DatabaseInfo,
)

CONFD_USERNAME = "itde_confd"
# 1000-range UIDs are commonly already used by container images.
CONFD_USER_ID = 20001
CONFD_READINESS_ATTEMPTS = 12


class CreateConfdCredentials(DockerBaseTask):
    """Create the disposable ConfD account once the database is ready."""

    environment_name: str = luigi.Parameter()
    database_info: DatabaseInfo = JsonPickleParameter(DatabaseInfo, significant=False)  # type: ignore
    port_bind_address: str | None = luigi.OptionalParameter(
        default=None, significant=False
    )

    def run_task(self) -> None:
        if self.database_info.reused:
            raise RuntimeError(
                "Cannot create disposable ConfD credentials for a reused database"
            )
        if self.database_info.container_info is None:
            raise RuntimeError("Docker-DB container information is required for ConfD")

        self._wait_for_service_readiness()
        password = secrets.token_urlsafe(32)
        user_created = False
        try:
            self._create_user(password)
            user_created = True
            self._wait_for_rest_readiness(password)
            credentials_file = self._write_credentials_file(password)
        except Exception:
            if user_created:
                self._delete_user()
            raise

        forwarded_ports = self.database_info.forwarded_ports
        confd_port = None if forwarded_ports is None else forwarded_ports.confd
        endpoint = None
        if confd_port is not None:
            endpoint = (
                f"https://{self.port_bind_address or '127.0.0.1'}:{confd_port}/RPC2"
            )
        self.return_object(
            ConfdInfo(
                username=CONFD_USERNAME,
                credentials_file=str(credentials_file),
                tunnel_target_host=self.database_info.host,
                endpoint=endpoint,
            )
        )

    def _create_user(self, password: str) -> None:
        command = (
            "confd_client -c user_create -A "
            f'\'{{"username":"{CONFD_USERNAME}","userid":{CONFD_USER_ID},'
            '"group":"exaadm","login_enabled":true,"password":"\''
            '"$CONFD_PASSWORD"'
            '\'","encode_passwd":true}\''
        )
        self._wait_for_readiness(
            command,
            {"CONFD_PASSWORD": password},
            "Disposable ConfD user could not be created",
        )

    def _delete_user(self) -> None:
        try:
            self._run_confd(
                f'confd_client -c user_delete -A \'{{"username":"{CONFD_USERNAME}"}}\''
            )
        except Exception:
            self.logger.warning("Unable to remove the disposable ConfD user")

    def _wait_for_service_readiness(self) -> None:
        command = (
            "status=$(curl --silent --output /dev/null --write-out '%{http_code}' "
            "--insecure --max-time 5 --header 'Content-Type: text/xml' "
            '--data-binary \'<?xml version="1.0"?><methodCall>'
            "<methodName>system.listMethods</methodName><params/></methodCall>' "
            '"https://$CONFD_HOST:443/RPC2"); test "$status" = 401'
        )
        self._wait_for_readiness(command, None, "ConfD service did not become ready")

    def _wait_for_rest_readiness(self, password: str) -> None:
        command = (
            "curl --fail --silent --show-error --insecure --max-time 5 "
            '--user "$CONFD_USERNAME:$CONFD_PASSWORD" '
            "--header 'Content-Type: text/xml' "
            '--data-binary \'<?xml version="1.0"?><methodCall>'
            "<methodName>system.listMethods</methodName><params/></methodCall>' "
            '"https://$CONFD_HOST:443/RPC2" >/dev/null'
        )
        self._wait_for_readiness(
            command,
            {
                "CONFD_USERNAME": CONFD_USERNAME,
                "CONFD_PASSWORD": password,
            },
            "ConfD REST endpoint did not become ready",
        )

    def _wait_for_readiness(
        self,
        command: str,
        environment: dict[str, str] | None,
        failure_message: str,
    ) -> None:
        for attempt in range(CONFD_READINESS_ATTEMPTS):
            try:
                self._run_confd(command, environment)
                return
            except RuntimeError:
                if attempt == CONFD_READINESS_ATTEMPTS - 1:
                    raise RuntimeError(failure_message)
                time.sleep(1)

    def _run_confd(
        self, command: str, environment: dict[str, str] | None = None
    ) -> None:
        if self.database_info.container_info is None:
            raise RuntimeError("Docker-DB container information is required for ConfD")
        with self._get_docker_client() as docker_client:
            container = docker_client.containers.get(
                self.database_info.container_info.container_name
            )
            command = (
                'export COS_DIRECTORY="$(dirname "$(dirname "$(command -v confd_client)")")"; '
                f"{command}"
            )
            result = container.exec_run(
                cmd=["/bin/sh", "-c", command],
                user="root",
                environment={
                    "CONFD_HOST": self.database_info.host,
                    # Docker-DB 7.1 can fail to resolve its generated container
                    # hostname while confd_client locates the single-node master.
                    "HOSTNAME": "localhost",
                    **(environment or {}),
                },
            )
        if result.exit_code != 0:
            output = result.output.decode("utf-8", errors="replace").strip()
            for value in (environment or {}).values():
                output = output.replace(value, "<redacted>")
            raise RuntimeError(f"Disposable ConfD user operation failed: {output}")

    def _write_credentials_file(self, password: str) -> Path:
        directory = self._credentials_file_path().parent
        directory.mkdir(parents=True, exist_ok=True)
        credentials_file = self._credentials_file_path()
        temporary_file = directory / ".confd_credentials.json.tmp"
        descriptor = os.open(
            temporary_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode=0o600
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as file:
                json.dump({"username": CONFD_USERNAME, "password": password}, file)
            os.replace(temporary_file, credentials_file)
            os.chmod(credentials_file, 0o600)
        except Exception:
            temporary_file.unlink(missing_ok=True)
            raise
        return credentials_file

    def cleanup_task(self, success: bool) -> None:
        if not success:
            self._credentials_file_path().unlink(missing_ok=True)

    def _credentials_file_path(self) -> Path:
        return Path(
            self.get_cache_path(),
            "environments",
            self.environment_name,
            "confd_credentials.json",
        )
