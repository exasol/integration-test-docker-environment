from dataclasses import dataclass
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")


@dataclass
class Option(Generic[T]):
    name: str
    prefix: str
    type: T
    default: Optional[T] = None
    help_text: str = ""

    @property
    def env_name(self):
        def normalize(name):
            name = name.replace("-", "_")
            name = name.upper()
            return name

        return f"{normalize(self.prefix)}_{normalize(self.name)}"

    @property
    def cli_name(self):
        def normalize(name):
            name = name.replace("_", "-")
            name = name.lower()
            return name

        return f"--{normalize(self.prefix)}-{normalize(self.name)}"

    @property
    def pytest_name(self):
        def normalize(name):
            name = name.replace("-", "_")
            name = name.lower()
            return name

        return f"{normalize(self.prefix)}_{normalize(self.name)}"

    @property
    def help(self):
        if not self.default:
            return f"{self.help_text}."
        return f"{self.help_text} (default: {self.default})."


@dataclass
class BucketFs:
    url: str
    username: str
    password: str


@dataclass
class Exasol:
    host: str
    port: int
    username: str
    password: str


@dataclass
class Itde:
    db: Exasol
    bucketfs: BucketFs
    schemas: List[str]
    bootstrap: bool
