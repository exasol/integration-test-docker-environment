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
    def env(self):
        """Environment variable name"""

        def normalize(name):
            name = name.replace("-", "_")
            name = name.upper()
            return name

        return f"{normalize(self.prefix)}_{normalize(self.name)}"

    @property
    def cli(self):
        """Cli argument name"""

        def normalize(name):
            name = name.replace("_", "-")
            name = name.lower()
            return name

        return f"--{normalize(self.prefix)}-{normalize(self.name)}"

    @property
    def pytest(self):
        """Pytest option name"""

        def normalize(name):
            name = name.replace("-", "_")
            name = name.lower()
            return name

        return f"{normalize(self.prefix)}_{normalize(self.name)}"

    @property
    def help(self):
        """Help text including information about default value."""
        if not self.default:
            return f"{self.help_text}."
        return f"{self.help_text} (default: {self.default})."


class OptionGroup:
    def __init__(self, prefix, options):
        self._prefix = prefix
        self._options = (Option(prefix=prefix, **kwargs) for kwargs in options)

    @property
    def prefix(self):
        return self._prefix

    @property
    def options(self):
        return self._options


@dataclass
class Exasol:
    host: str
    port: int
    username: str
    password: str


@dataclass
class BucketFs:
    url: str
    username: str
    password: str


@dataclass
class Itde:
    db_version: str
    schemas: List[str]
    db: Exasol
    bucketfs: BucketFs
