from collections import ChainMap
from dataclasses import dataclass
from typing import Generic, List, Optional, TypeVar

from pyexasol.connection import ExaConnection

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
        self._options = tuple(Option(prefix=prefix, **kwargs) for kwargs in options)
        self._default = {o.name: o.default for o in self._options}
        self._env = {}
        self._cli = {}
        self._kwargs = ChainMap(self._cli, self._env, self._default)

    @property
    def prefix(self):
        return self._prefix

    @property
    def options(self):
        return self._options

    def kwargs(self, environment, cli_arguments):
        env = {
            o.name: o.type(environment[o.env])
            for o in self._options
            if o.env in environment
        }
        cli = {
            o.name: getattr(cli_arguments, o.pytest)
            for o in self.options
            if hasattr(cli_arguments, o.pytest)
            and getattr(cli_arguments, o.pytest) is not None
        }
        self._env.update(env)
        self._cli.update(cli)
        return self._kwargs


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


@dataclass
class TestConfig:
    db: Exasol
    bucketfs: BucketFs
    itde: Itde
    ctrl_connection: ExaConnection
