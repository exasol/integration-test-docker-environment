import json
import stat
from pathlib import Path

from exasol_integration_test_docker_environment.lib.base.info import Info


class ConfdCredentials:
    """Credentials read from ITDE's owner-only disposable secret file."""

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(username={self.username!r}, password=<redacted>)"


class ConfdInfo(Info):
    """Non-secret connection metadata for the disposable ConfD account."""

    def __init__(
        self,
        username: str,
        credentials_file: str,
        tunnel_target_host: str,
        tunnel_target_port: int = 443,
        endpoint: str | None = None,
    ) -> None:
        self.username = username
        self.credentials_file = credentials_file
        self.tunnel_target_host = tunnel_target_host
        self.tunnel_target_port = tunnel_target_port
        self.endpoint = endpoint

    def read_credentials(self) -> ConfdCredentials:
        """Read credentials after verifying that no other user can read the file."""
        path = Path(self.credentials_file)
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode & 0o077:
            raise PermissionError(
                f"ConfD credentials file '{path}' must be owner-only, got {mode:o}"
            )
        with path.open(encoding="utf-8") as credentials_file:
            credentials = json.load(credentials_file)
        return ConfdCredentials(credentials["username"], credentials["password"])

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(username={self.username!r}, "
            f"credentials_file={self.credentials_file!r}, "
            f"tunnel_target_host={self.tunnel_target_host!r}, "
            f"tunnel_target_port={self.tunnel_target_port!r}, "
            f"endpoint={self.endpoint!r})"
        )
