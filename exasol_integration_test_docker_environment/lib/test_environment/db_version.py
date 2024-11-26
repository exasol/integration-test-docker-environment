from typing import (
    Optional,
    Tuple,
)

from exasol_integration_test_docker_environment.cli.options.test_environment_options import (
    LATEST_DB_VERSION,
)

DEFAULT_VERSION = "default"


class DbVersion:
    def __init__(self, major, minor, stable):
        self.major = major
        self.minor = minor
        self.stable = stable

    @classmethod
    def from_db_version_str(cls, db_version_str: Optional[str]):
        db_version: str = (
            LATEST_DB_VERSION if db_version_str is None else db_version_str
        )
        if db_version_str == DEFAULT_VERSION:
            db_version = LATEST_DB_VERSION
        if db_version.endswith("-d1"):
            db_version = "-".join(db_version.split("-")[0:-1])
        if db_version.startswith("prerelease-"):
            db_version = "-".join(db_version.split("-")[1:])
        version: Tuple[int, ...] = tuple([int(v) for v in db_version.split(".")])
        if len(version) != 3:
            raise ValueError(f"Invalid db version given: {db_version}")
        return DbVersion(version[0], version[1], version[2])

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.stable}"

    def to_tuple(self):
        return self.major, self.minor, self.stable

    def __eq__(self, other) -> bool:
        return self.to_tuple() == other.to_tuple()

    def __lt__(self, other) -> bool:
        return self.to_tuple() < other.to_tuple()

    def __le__(self, other) -> bool:
        return self.to_tuple() <= other.to_tuple()

    def __ge__(self, other) -> bool:
        return self.to_tuple() >= other.to_tuple()

    def __gt__(self, other) -> bool:
        return self.to_tuple() > other.to_tuple()


def db_version_supports_custom_certificates(db_version_str: Optional[str]) -> bool:
    return DbVersion.from_db_version_str(db_version_str) > DbVersion(7, 0, 5)
