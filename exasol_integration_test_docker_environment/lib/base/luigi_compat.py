"""
Minimal re-implementation of the Luigi API used in this project.
Replace ``import luigi`` with ``from ... import luigi_compat as luigi`` or use
the individual names exported from this module.
"""
from __future__ import annotations

import hashlib
import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TASK_ID_TRUNCATE_HASH: int = 10


# ---------------------------------------------------------------------------
# Parameter visibility
# ---------------------------------------------------------------------------

class ParameterVisibility(Enum):
    PUBLIC = "public"
    HIDDEN = "hidden"
    PRIVATE = "private"


# ---------------------------------------------------------------------------
# Sentinel for "no default value"
# ---------------------------------------------------------------------------

_no_value: object = object()


# ---------------------------------------------------------------------------
# Parameter classes
# ---------------------------------------------------------------------------

class Parameter:
    """Base parameter descriptor.

    The constructor signature intentionally matches Luigi's ``Parameter`` so
    that ``JsonPickleParameter`` can call ``super().__init__()`` with
    positional arguments without changes.
    """

    def __init__(
        self,
        default: Any = _no_value,
        is_global: bool = False,
        significant: bool = True,
        description: Optional[str] = None,
        config_path: Optional[dict] = None,
        positional: bool = True,
        always_in_help: bool = False,
        batch_method: Any = None,
        visibility: ParameterVisibility = ParameterVisibility.PUBLIC,
    ) -> None:
        self.default = default
        self.significant = significant
        self.description = description
        self.visibility = visibility
        # unused but accepted for compatibility
        self._is_global = is_global
        self._config_path = config_path
        self._positional = positional
        self._always_in_help = always_in_help
        self._batch_method = batch_method

    def normalize(self, value: Any) -> Any:
        return value

    def parse(self, s: str) -> Any:
        return s

    def serialize(self, x: Any) -> str:
        return str(x)


class BoolParameter(Parameter):
    _TRUE = {"true", "1", "yes"}

    def normalize(self, value: Any) -> bool:
        if isinstance(value, str):
            return value.lower() in self._TRUE
        return bool(value)

    def parse(self, s: str) -> bool:
        return s.lower() in self._TRUE

    def serialize(self, x: Any) -> str:
        return str(bool(x))


class IntParameter(Parameter):
    def normalize(self, value: Any) -> int:
        return int(value)

    def parse(self, s: str) -> int:
        return int(s)

    def serialize(self, x: Any) -> str:
        return str(int(x))


class ListParameter(Parameter):
    """List parameter — normalises to ``tuple`` for hashability."""

    def normalize(self, value: Any) -> tuple:
        if value is None:
            return ()
        return tuple(value)

    def parse(self, s: str) -> tuple:
        return tuple(json.loads(s))

    def serialize(self, x: Any) -> str:
        return json.dumps(list(x))


class DictParameter(Parameter):
    def normalize(self, value: Any) -> dict:
        if value is None:
            return {}
        return dict(value)

    def parse(self, s: str) -> dict:
        return dict(json.loads(s))

    def serialize(self, x: Any) -> str:
        return json.dumps(dict(x))


class OptionalParameter(Parameter):
    """Parameter whose value may be ``None`` / empty."""

    def normalize(self, value: Any) -> Optional[str]:
        if value == "" or value is None:
            return None
        return str(value)

    def parse(self, s: str) -> Optional[str]:
        if s == "" or s is None:
            return None
        return s

    def serialize(self, x: Any) -> str:
        if x is None:
            return ""
        return str(x)


class EnumParameter(Parameter):
    """Parameter for Python ``Enum`` types."""

    def __init__(self, enum: type, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._enum = enum

    def normalize(self, value: Any) -> Any:
        if isinstance(value, self._enum):
            return value
        return self._enum[str(value)]

    def parse(self, s: str) -> Any:
        return self._enum[s]

    def serialize(self, x: Any) -> str:
        return x.name if isinstance(x, Enum) else str(x)


# ---------------------------------------------------------------------------
# I/O format stub (used by PickleTarget)
# ---------------------------------------------------------------------------

class NopFormat:
    """Stub that signals binary (pass-through) I/O to LocalTarget."""
    pass


# ---------------------------------------------------------------------------
# Metaclass that collects Parameter descriptors
# ---------------------------------------------------------------------------

class _TaskMeta(type):
    """Walks the MRO and collects all ``Parameter`` instances into ``_params``."""

    def __new__(
        mcs,
        name: str,
        bases: tuple,
        namespace: dict,
    ) -> "_TaskMeta":
        cls = super().__new__(mcs, name, bases, namespace)
        params: dict[str, Parameter] = {}
        for base in reversed(cls.__mro__):
            for attr, val in vars(base).items():
                if isinstance(val, Parameter):
                    params[attr] = val
        cls._params: dict[str, Parameter] = params
        return cls


# ---------------------------------------------------------------------------
# Task base class
# ---------------------------------------------------------------------------

class Task(metaclass=_TaskMeta):
    """Minimal replacement for ``luigi.Task``."""

    def __init__(self, **kwargs: Any) -> None:
        for name, param in type(self)._params.items():
            if name in kwargs:
                setattr(self, name, param.normalize(kwargs[name]))
            elif param.default is not _no_value:
                setattr(self, name, param.normalize(param.default))
            else:
                raise ValueError(
                    f"Required parameter '{name}' not provided for "
                    f"{type(self).__name__}"
                )
        # Compute initial task_id (may be overridden by BaseTask subclass)
        self.task_id: str = _compute_task_id(
            self.get_task_family(), self._get_significant_params()
        )

    # ------------------------------------------------------------------
    # Class-level helpers
    # ------------------------------------------------------------------

    @classmethod
    def get_task_family(cls) -> str:
        return cls.__name__

    @classmethod
    def get_params(cls) -> list[tuple[str, Parameter]]:
        return list(cls._params.items())

    @classmethod
    def get_param_values(
        cls,
        params: list[tuple[str, Parameter]],
        args: list,
        kwargs: dict,
    ) -> list[tuple[str, Any]]:
        """Return ``[(name, value), ...]`` for all params present in *kwargs*."""
        return [(name, kwargs[name]) for name, _ in params if name in kwargs]

    # ------------------------------------------------------------------
    # Instance helpers
    # ------------------------------------------------------------------

    @property
    def param_kwargs(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in type(self)._params}

    def _get_significant_params(self) -> dict[str, str]:
        return {
            name: param.serialize(getattr(self, name))
            for name, param in type(self)._params.items()
            if param.significant
        }

    # ------------------------------------------------------------------
    # Luigi Task interface
    # ------------------------------------------------------------------

    def complete(self) -> bool:
        outputs = self.output()
        if not outputs:
            return True
        if isinstance(outputs, list):
            return all(t.exists() for t in outputs)
        if isinstance(outputs, dict):
            return all(t.exists() for t in outputs.values())
        return outputs.exists()

    def requires(self) -> list:
        return []

    def output(self) -> Any:
        return []

    def run(self) -> None:
        pass

    def on_success(self) -> None:
        pass

    def on_failure(self, exception: Exception) -> None:
        pass


# ---------------------------------------------------------------------------
# Config class
# ---------------------------------------------------------------------------

class Config(Task):
    """Replacement for ``luigi.Config``.

    Parameters are filled from the global configuration store when not
    supplied as constructor keyword arguments.  Can also be used as a
    multiple-inheritance mixin alongside ``BaseTask`` subclasses.
    """

    def __init__(self, **kwargs: Any) -> None:
        section = type(self).__name__
        for name, param in type(self)._params.items():
            if name not in kwargs:
                raw = get_config().get(section, name)
                if raw is not None:
                    kwargs[name] = param.parse(raw)
        super().__init__(**kwargs)


# ---------------------------------------------------------------------------
# LocalTarget
# ---------------------------------------------------------------------------

class LocalTarget:
    """Replacement for ``luigi.LocalTarget``."""

    def __init__(
        self,
        path: Any,
        format: Any = None,
        is_tmp: bool = False,
    ) -> None:
        self.path: str = str(path)
        self._format = format
        self._is_tmp = is_tmp

    def exists(self) -> bool:
        return os.path.exists(self.path)

    def open(self, mode: str):
        """Return a file object.

        Uses binary mode when a ``NopFormat`` was supplied (as ``PickleTarget``
        does), otherwise text mode with UTF-8 encoding.
        """
        binary = isinstance(self._format, NopFormat)
        if mode == "w":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            return open(self.path, "wb" if binary else "w", **(
                {} if binary else {"encoding": "utf-8"}
            ))
        # read
        return open(self.path, "rb" if binary else "r", **(
            {} if binary else {"encoding": "utf-8"}
        ))


# ---------------------------------------------------------------------------
# Global configuration store
# ---------------------------------------------------------------------------

_config_store: dict[tuple[str, str], str] = {}


class ConfigurationManager:
    """Replacement for the object returned by ``luigi.configuration.get_config()``."""

    def set(self, section: str, key: str, value: str) -> None:
        _config_store[(section.lower(), key.lower())] = str(value)

    def get(
        self,
        section: str,
        key: str,
        default: Optional[str] = None,
    ) -> Optional[str]:
        return _config_store.get((section.lower(), key.lower()), default)


_config_manager = ConfigurationManager()


def get_config() -> ConfigurationManager:
    """Return the singleton :class:`ConfigurationManager`."""
    return _config_manager


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def flatten(struct: Any) -> list:
    """Recursively flatten a nested structure of Tasks into a flat list."""
    if struct is None:
        return []
    if isinstance(struct, Task):
        return [struct]
    if isinstance(struct, dict):
        result: list = []
        for v in struct.values():
            result.extend(flatten(v))
        return result
    if isinstance(struct, (list, tuple)):
        result = []
        for item in struct:
            result.extend(flatten(item))
        return result
    return []


def common_params(task_instance: Task, task_class: type) -> dict[str, Any]:
    """Return ``{name: value}`` for params present in both instance and class."""
    class_param_names = {name for name, _ in task_class.get_params()}
    return {
        name: getattr(task_instance, name)
        for name in type(task_instance)._params
        if name in class_param_names
    }


def _compute_task_id(task_family: str, significant_params: dict[str, str]) -> str:
    param_str = json.dumps(significant_params, separators=(",", ":"), sort_keys=True)
    param_hash = hashlib.sha3_256(param_str.encode("utf-8")).hexdigest()
    return f"{task_family}_{param_hash[:TASK_ID_TRUNCATE_HASH]}"


# ---------------------------------------------------------------------------
# Namespace shims — allow ``luigi.configuration.get_config()``, etc.
# ---------------------------------------------------------------------------

class configuration:  # noqa: N801
    """Shim for ``luigi.configuration``."""
    get_config = staticmethod(get_config)


class task:  # noqa: N801
    """Shim for ``luigi.task``."""
    TASK_ID_TRUNCATE_HASH = TASK_ID_TRUNCATE_HASH
    flatten = staticmethod(flatten)


class util:  # noqa: N801
    """Shim for ``luigi.util``."""
    common_params = staticmethod(common_params)


class parameter:  # noqa: N801
    """Shim for ``luigi.parameter``."""
    ParameterVisibility = ParameterVisibility
    _no_value = _no_value
    UnconsumedParameterWarning = UserWarning  # stub — configure_logging is rewritten


# Expose the format module shim
class format:  # noqa: N801
    NopFormat = NopFormat


# ---------------------------------------------------------------------------
# Target — abstract base for non-file-based targets (e.g. DockerImageTarget)
# ---------------------------------------------------------------------------

class Target:
    """Replacement for ``luigi.Target``."""

    def exists(self) -> bool:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# build() shim — allows test code to call luigi.build(...) unchanged
# ---------------------------------------------------------------------------

def build(tasks: list, workers: int = 1, **_ignored) -> bool:
    from exasol_integration_test_docker_environment.lib.base import ray_runner  # lazy to avoid circular import
    return ray_runner.build(tasks, workers=workers)
