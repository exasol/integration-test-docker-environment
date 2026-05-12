from __future__ import annotations

import hashlib
import json
import logging
import shutil
from collections.abc import Generator
from pathlib import Path
from typing import (
    Any,
    TypeVar,
)

from exasol_integration_test_docker_environment.abstract_method_exception import (
    AbstractMethodException,
)
from exasol_integration_test_docker_environment.lib.base.abstract_task_future import (
    AbstractTaskFuture,
)
from exasol_integration_test_docker_environment.lib.base.pickle_target import (
    PickleTarget,
)
from exasol_integration_test_docker_environment.lib.base.task_logger_wrapper import (
    TaskLoggerWrapper,
)
from exasol_integration_test_docker_environment.lib.base.task_state import TaskState
from exasol_integration_test_docker_environment.lib.base.wrong_task_state_exception import (
    WrongTaskStateException,
)
from exasol_integration_test_docker_environment.lib.models.config.build_config import (
    build_config,
)

COMPLETION_TARGET = "completion_target"

RUN_DEPENDENCIES = "run_dependencies"


class RequiresTaskFuture(AbstractTaskFuture):
    """
    Represents a future for a statically registered child task.
    """

    def __init__(self, current_task: RayBaseTask, child_task_index: int) -> None:
        self._child_task_index = child_task_index
        self._current_task = current_task
        self._outputs_cache = None

    def get_output(self) -> Any:
        if self._current_task._task_state == TaskState.RUN:
            if self._outputs_cache is None:
                child_task = self._current_task._registered_tasks[
                    self._child_task_index
                ]
                completion_target = child_task.output()
                self._outputs_cache = completion_target.read()
            return self._outputs_cache
        raise WrongTaskStateException(
            self._current_task._task_state, "RequiresTaskFuture.read_outputs_dict"
        )


class RunTaskFuture(AbstractTaskFuture):
    """
    Represents a future for a dynamically registered child task.
    """

    def __init__(self, completion_target: PickleTarget) -> None:
        self._outputs_cache = None
        self.completion_target = completion_target

    def get_output(self) -> Any:
        if self._outputs_cache is None:
            self._outputs_cache = self.completion_target.read()
        return self._outputs_cache


RayBaseTaskType = TypeVar("RayBaseTaskType", bound="RayBaseTask")


class RayBaseTask:
    caller_output_path: tuple[str, ...]
    job_id: str

    def __init__(self, **kwargs) -> None:
        self._registered_tasks: list[RayBaseTask] = []
        self._run_dependencies_tasks: list[RayBaseTask] = []
        self._task_state = TaskState.INIT
        self.caller_output_path = tuple(kwargs.pop("caller_output_path", ()))
        try:
            self.job_id = kwargs.pop("job_id")
        except KeyError as exc:
            raise TypeError("job_id is required") from exc
        self._task_kwargs = dict(kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.task_id = self.task_id_str(
            self.get_task_family(), self.get_parameter_as_string_dict()
        )
        self.__hash = hash(self.task_id)
        self._init_non_pickle_attributes()
        self.register_required()
        self._task_state = TaskState.AFTER_INIT

    @classmethod
    def get_task_family(cls) -> str:
        return cls.__name__

    @classmethod
    def _declared_parameter_names(cls) -> set[str]:
        names: set[str] = set()
        for base in reversed(cls.__mro__):
            names.update(getattr(base, "__annotations__", {}).keys())
        return {
            name
            for name in names
            if name not in {"caller_output_path", "job_id"} and not name.startswith("_")
        }

    def _init_non_pickle_attributes(self) -> None:
        logger = logging.getLogger(f"ray-interface.{self.__class__.__name__}")
        self.logger = TaskLoggerWrapper(logger, self.__repr__())
        self._run_dependencies_target = PickleTarget(
            path=self._get_tmp_path_for_run_dependencies()
        )
        self._complete_target = PickleTarget(
            path=self._get_tmp_path_for_completion_target()
        )
        self._registered_return_target = None

    def __getstate__(self):
        new_dict = dict(self.__dict__)
        del new_dict["logger"]
        del new_dict["_complete_target"]
        del new_dict["_run_dependencies_target"]
        return new_dict

    def __setstate__(self, new_dict):
        self.__dict__ = new_dict
        self._init_non_pickle_attributes()

    def task_id_str(self, task_family: str, params: dict[str, str]) -> str:
        param_str = json.dumps(params, separators=(",", ":"), sort_keys=True)
        param_hash = hashlib.sha3_256(param_str.encode("utf-8")).hexdigest()
        return f"{task_family}_{param_hash[:10]}"

    def get_parameter_as_string_dict(self) -> dict[str, str]:
        params_str: dict[str, str] = {}
        for param_name in sorted(
            self._declared_parameter_names() | {"caller_output_path", "job_id"}
        ):
            if hasattr(self, param_name):
                params_str[param_name] = self._serialize_value(
                    getattr(self, param_name)
                )
        return params_str

    def _serialize_value(self, value: Any) -> str:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return json.dumps(value, separators=(",", ":"))
        if isinstance(value, tuple):
            return json.dumps(
                [self._serialize_value(item) for item in value], separators=(",", ":")
            )
        if isinstance(value, list):
            return json.dumps(
                [self._serialize_value(item) for item in value], separators=(",", ":")
            )
        if isinstance(value, dict):
            return json.dumps(
                {
                    key: self._serialize_value(item)
                    for key, item in sorted(value.items())
                },
                separators=(",", ":"),
                sort_keys=True,
            )
        return json.dumps(str(value), separators=(",", ":"))

    def get_output_path(self) -> Path:
        path = Path(
            self._get_output_path_for_job(),
            "outputs",
            Path(*self._extend_output_path()),
        )
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _get_output_path_for_job(self) -> Path:
        return Path(build_config().output_directory, "jobs", self.job_id)

    def _extend_output_path(self) -> tuple[str, ...] | str:
        extension = self.extend_output_path()
        if extension is None or extension == ():
            return self.task_id
        return extension

    def extend_output_path(self) -> tuple[str, ...]:
        return tuple(self.caller_output_path) + (self.task_id,)

    def _get_tmp_path_for_job(self) -> Path:
        return Path(self._get_output_path_for_job(), "temp")

    def _get_tmp_path_for_task(self) -> Path:
        return Path(self._get_tmp_path_for_job(), self.task_id)

    def _get_tmp_path_for_completion_target(self) -> Path:
        return Path(self._get_tmp_path_for_task(), COMPLETION_TARGET)

    def _get_tmp_path_for_run_dependencies(self) -> Path:
        return Path(self._get_tmp_path_for_task(), RUN_DEPENDENCIES)

    def get_log_path(self) -> Path:
        path = Path(self.get_output_path(), "logs")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_cache_path(self) -> Path:
        path = Path(str(build_config().output_directory), "cache")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def register_required(self) -> None:
        pass

    def register_dependency(self, task: RayBaseTaskType) -> RequiresTaskFuture:
        if self._task_state == TaskState.INIT:
            index = len(self._registered_tasks)
            self._registered_tasks.append(task)
            return RequiresTaskFuture(self, index)
        raise WrongTaskStateException(self._task_state, "register_dependency")

    def register_dependencies(self, tasks) -> Any:
        if isinstance(tasks, dict):
            return {
                key: self.register_dependencies(task) for key, task in tasks.items()
            }
        if isinstance(tasks, list):
            return [self.register_dependencies(task) for task in tasks]
        if isinstance(tasks, tuple):
            return tuple(self.register_dependencies(task) for task in tasks)
        if isinstance(tasks, RayBaseTask):
            return self.register_dependency(tasks)
        return tasks

    def get_values_from_futures(self, futures) -> Any:
        if isinstance(futures, dict):
            return {
                key: self.get_values_from_futures(task) for key, task in futures.items()
            }
        if isinstance(futures, list):
            return [self.get_values_from_futures(task) for task in futures]
        if isinstance(futures, tuple):
            return tuple(self.get_values_from_futures(task) for task in futures)
        if isinstance(futures, AbstractTaskFuture):
            return self.get_values_from_future(futures)
        return futures

    def get_values_from_future(self, future: AbstractTaskFuture) -> Any:
        return future.get_output()

    def requires(self):
        return self._registered_tasks

    def output(self):
        return self._complete_target

    def run(self):
        try:
            self._task_state = TaskState.RUN
            task_generator = self.run_task()
            if task_generator is not None:
                yield from task_generator
            self._task_state = TaskState.FINISHED
            self.logger.info("Write complete_target")
            self._complete_target.write(self._registered_return_target)
        except Exception as e:
            self._task_state = TaskState.ERROR
            self.logger.exception("Exception in run: %s", e)
            raise e

    def run_task(self):
        raise AbstractMethodException()

    def run_dependencies(self, tasks) -> Generator[RayBaseTaskType, Any, Any]:
        if self._task_state == TaskState.RUN:
            self._register_run_dependencies(tasks)
            self._run_dependencies_target.write(self._run_dependencies_tasks)
            completion_targets = yield tasks
            task_futures = self._generate_run_task_futures(completion_targets)
            return task_futures
        raise WrongTaskStateException(self._task_state, "run_dependency")

    def _register_run_dependencies(self, tasks: Any) -> None:
        if isinstance(tasks, dict):
            for task in tasks.values():
                self._register_run_dependencies(task)
        elif isinstance(tasks, list):
            for task in tasks:
                self._register_run_dependencies(task)
        elif isinstance(tasks, tuple):
            for task in tasks:
                self._register_run_dependencies(task)
        elif isinstance(tasks, RayBaseTask):
            self._run_dependencies_tasks.append(tasks)

    def _generate_run_task_futures(
        self, completion_targets: Any
    ) -> list[Any] | dict[Any, Any] | RunTaskFuture | Any:
        if isinstance(completion_targets, dict):
            return {
                key: self._generate_run_task_futures(task)
                for key, task in completion_targets.items()
            }
        if isinstance(completion_targets, list):
            return [
                self._generate_run_task_futures(task) for task in completion_targets
            ]
        if isinstance(completion_targets, tuple):
            return tuple(
                self._generate_run_task_futures(task) for task in completion_targets
            )
        if isinstance(completion_targets, PickleTarget):
            return RunTaskFuture(completion_targets)
        return completion_targets

    def return_object(self, object: Any) -> None:
        """
        Returns the object to the calling task. The object needs to be pickleable.
        """
        if self._task_state == TaskState.RUN:
            if self._registered_return_target is None:
                self._registered_return_target = object
            else:
                raise Exception("return target already used")
        else:
            raise WrongTaskStateException(self._task_state, "return_target")

    def get_result(self) -> Any:
        """
        Returns the single value passed with return_object() during run_task().
        """
        if not self.output().exists():
            raise WrongTaskStateException(TaskState.NONE, "get_result")
        return self.output().read()

    def __repr__(self) -> str:
        params = self.get_parameter_as_string_dict()
        repr_parts = []
        for param_name, param_value in sorted(params.items()):
            if param_name in {"job_id", "caller_output_path"}:
                continue
            repr_parts.append(f"{param_name}={param_value}")
        return f"{self.task_id}({', '.join(repr_parts)})"

    def create_child_task_with_common_params(
        self, task_class: type[RayBaseTaskType], **kwargs
    ) -> RayBaseTaskType:
        params = self._common_params_for(task_class)
        params["caller_output_path"] = self._extend_output_path()
        params["job_id"] = self.job_id
        params.update(kwargs)
        return task_class(**params)

    def create_child_task(
        self, task_class: type[RayBaseTaskType], **kwargs
    ) -> RayBaseTaskType:
        params: dict[str, Any] = {}
        params["caller_output_path"] = self._extend_output_path()
        params["job_id"] = self.job_id
        params.update(kwargs)
        return task_class(**params)

    def _common_params_for(self, task_class: type[RayBaseTaskType]) -> dict[str, Any]:
        common: dict[str, Any] = {}
        for param_name in self._declared_parameter_names():
            if (
                hasattr(self, param_name)
                and param_name in task_class._declared_parameter_names()
            ):
                common[param_name] = getattr(self, param_name)
        return common

    def cleanup(self, success: bool) -> None:
        self.cleanup_internal(success, set())

    def cleanup_internal(self, success: bool, cleanup_checklist: set[str]) -> None:
        self.logger.debug("Cleaning up")
        if str(self) not in cleanup_checklist:
            cleanup_checklist.add(str(self))
            if (
                self._task_state != TaskState.CLEANUP
                and self._task_state != TaskState.CLEANED
            ):
                self._task_state = TaskState.CLEANUP
                try:
                    self.cleanup_child_task(success, cleanup_checklist)
                except Exception as e:
                    self.logger.error("Error during cleaning up child tasks", e)
                try:
                    self.cleanup_task(success)
                except Exception as e:
                    self.logger.error("Error during cleaning up task", e)
                if self._get_tmp_path_for_task().exists():
                    shutil.rmtree(self._get_tmp_path_for_task())
                self._task_state = TaskState.CLEANED
            self.logger.debug("Cleanup finished")
        else:
            self.logger.debug("Cleanup skipped")

    def cleanup_child_task(self, success: bool, cleanup_checklist: set[str]) -> None:
        if self._run_dependencies_target.exists():
            run_dependencies_tasks_from_target = self._run_dependencies_target.read()
        else:
            run_dependencies_tasks_from_target = []
        run_dependencies_tasks = (
            self._run_dependencies_tasks + run_dependencies_tasks_from_target
        )
        reversed_run_dependencies_task_list = list(run_dependencies_tasks)
        reversed_run_dependencies_task_list.reverse()
        for task in reversed_run_dependencies_task_list:
            task.cleanup_internal(success, cleanup_checklist)

        reversed_registered_task_list = list(self._registered_tasks)
        reversed_registered_task_list.reverse()
        for task in reversed_registered_task_list:
            task.cleanup_internal(success, cleanup_checklist)

    def cleanup_task(self, success: bool) -> None:
        pass
