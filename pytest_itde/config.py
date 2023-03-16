from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class Option(Generic[T]):
    name: str
    prefix: str
    type: T
    default: Optional[T] = None
    help: str = ""

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
    schemas: str


@dataclass
class Itde:
    db: Exasol
    bucketfs: BucketFs
