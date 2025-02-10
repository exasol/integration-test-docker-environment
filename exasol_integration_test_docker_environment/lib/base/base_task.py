import hashlib
import json
import logging
import shutil
from pathlib import Path
from typing import (
    Any,
    Dict,
    Generator,
    List,
    Set,
    Union,
)

import luigi
import six
from luigi import (
    Task,
    util,
)
from luigi.parameter import ParameterVisibility
from luigi.task import TASK_ID_TRUNCATE_HASH

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
from exasol_integration_test_docker_environment.lib.config.build_config import (
    build_config,
)

RETURN_TARGETS = "return_targets"

COMPLETION_TARGET = "completion_target"

RUN_DEPENDENCIES = "run_dependencies"


class RequiresTaskFuture(AbstractTaskFuture):
    """
    Represents a future for a statically ("requires") registered task.
    Details:
    - The RegisterTaskFuture is used with dependencies returned in luigis required method
    - In the required method you return tasks and usually you would to get the output target of your child tasks
      via luigis input() method (check https://luigi.readthedocs.io/en/stable/tasks.html#task-input)
    - However, if you have multiple child tasks which return in requires, for example in a dict or list,
      you need address each task in the input first and then you address the output
    - output can also return a nested dict or list of targets
    - requires can return a nested dict or list of tasks
    - we reduced the output to a single completion target with the list of return value targets
      and the child tasks are collected in the registered_tasks list
    - The RegisterTaskFuture gets the position of the task in the registered_tasks as input, such as current task
    - If the user call get_output the RegisterTaskFuture call the input() method of the current task and
       uses the position of child task to retrieve the completion target of the child task
    - It then reads the completion target to get the list of return value targets and reads the requested one.
    """

    def __init__(self, current_task: "BaseTask", child_task_index: int):
        self._child_task_index = child_task_index
        self._current_task = current_task
        self._outputs_cache = None

    def get_output(self) -> Any:
        if self._current_task._task_state == TaskState.RUN:
            if self._outputs_cache is None:
                completion_target = self._current_task.input()[self._child_task_index]
                self._outputs_cache = completion_target.read()
            return self._outputs_cache
        else:
            raise WrongTaskStateException(
                self._current_task._task_state, "RequiresTaskFuture.read_outputs_dict"
            )


class RunTaskFuture(AbstractTaskFuture):
    """
    Represents a future for a dynamically registered task.
    Details:
    - run_dependencies uses luigi dynamic task by yielding the tasks
    - luigi returns for each yielded task the return value of that tasks output method
      (see https://luigi.readthedocs.io/en/stable/tasks.html#dynamic-dependencies)
    - the output method returns targets and in case of the BaseTask this is always the completion target
      which contains the list of return value targets
    - the RunTaskFuture encapsulate the target returned by the yield and handles reading the target for the user,
      such that the user get directly the return values of the child task

    """

    def __init__(self, completion_target: PickleTarget):
        self._outputs_cache = None
        self.completion_target = completion_target

    def get_output(self) -> Any:
        if self._outputs_cache is None:
            self._outputs_cache = self.completion_target.read()
        return self._outputs_cache


class BaseTask(Task):
    caller_output_path: List[str] = luigi.ListParameter([], significant=False, visibility=ParameterVisibility.HIDDEN)  # type: ignore
    job_id: str = luigi.Parameter()  # type: ignore

    def __init__(self, *args, **kwargs):
        self._registered_tasks = []
        self._run_dependencies_tasks = []
        self._task_state = TaskState.INIT
        super().__init__(*args, **kwargs)
        self.task_id = self.task_id_str(
            self.get_task_family(), self.get_parameter_as_string_dict()
        )
        self.__hash = hash(self.task_id)
        self._init_non_pickle_attributes()
        self.register_required()
        self._task_state = TaskState.AFTER_INIT

    def _init_non_pickle_attributes(self):
        logger = logging.getLogger(f"luigi-interface.{self.__class__.__name__}")
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

    def task_id_str(self, task_family, params):
        """
        Returns a canonical string used to identify a particular task

        :param task_family: The task family (class name) of the task
        :param params: a dict mapping parameter names to their serialized values
        :return: A unique, shortened identifier corresponding to the family and params
        """
        # task_id is a concatenation of task family, the first values of the first 3 parameters
        # sorted by parameter name and a md5hash of the family/parameters as a cananocalised json.
        param_str = json.dumps(params, separators=(",", ":"), sort_keys=True)
        hash_input = param_str
        param_hash = hashlib.sha3_256(hash_input.encode("utf-8")).hexdigest()
        return f"{task_family}_{param_hash[:TASK_ID_TRUNCATE_HASH]}"

    def get_parameter_as_string_dict(self):
        """
        Convert all parameters to a str->str hash.
        """
        params_str = {}
        params = dict(self.get_params())
        for param_name, param_value in self.param_kwargs.items():
            if params[param_name].significant:
                params_str[param_name] = params[param_name].serialize(param_value)
        return params_str

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

    def _extend_output_path(self):
        extension = self.extend_output_path()
        if extension is None or extension == []:
            return self.task_id
        else:
            return extension

    def extend_output_path(self):
        return list(self.caller_output_path) + [self.task_id]

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

    def register_required(self):
        pass

    def register_dependency(self, task: "BaseTask") -> RequiresTaskFuture:
        """
        Registers a 'requires' (a static) dependency of the task. It returns a future which can be used in the
        run_task() method via BaseTask.get_values_from_future() to get access to the result of the child task.
        See class RequiresTaskFuture for more details.
        """
        if self._task_state == TaskState.INIT:
            index = len(self._registered_tasks)
            self._registered_tasks.append(task)
            return RequiresTaskFuture(self, index)
        else:
            raise WrongTaskStateException(self._task_state, "register_dependency")

    def register_dependencies(self, tasks):
        if isinstance(tasks, dict):
            return {
                key: self.register_dependencies(task) for key, task in tasks.items()
            }
        elif isinstance(tasks, list):
            return [self.register_dependencies(task) for task in tasks]
        elif isinstance(tasks, BaseTask):
            return self.register_dependency(tasks)
        else:
            return tasks

    def get_values_from_futures(self, futures):
        if isinstance(futures, dict):
            return {
                key: self.get_values_from_futures(task) for key, task in futures.items()
            }
        elif isinstance(futures, list):
            return [self.get_values_from_futures(task) for task in futures]
        elif isinstance(futures, AbstractTaskFuture):
            return self.get_values_from_future(futures)
        else:
            return futures

    def get_values_from_future(
        self, future: AbstractTaskFuture
    ) -> Union[Any, Set[str]]:
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

    def run_dependencies(self, tasks) -> Generator["BaseTask", PickleTarget, Any]:
        """
        Runs a 'run' (a dynamic) dependency
        (that means a dependencies which was evaluated during the runtime of the task), and returns a RunTaskFuture.
        The returned future can then be used with BaseTask.get_values_from_futures() to get access to the result
        of the child task.
        """
        if self._task_state == TaskState.RUN:
            self._register_run_dependencies(tasks)
            self._run_dependencies_target.write(self._run_dependencies_tasks)
            completion_targets = yield tasks
            task_futures = self._generate_run_task_futures(completion_targets)
            return task_futures
        else:
            raise WrongTaskStateException(self._task_state, "run_dependency")

    def _register_run_dependencies(self, tasks):
        if isinstance(tasks, dict):
            for key, task in tasks.items():
                self._register_run_dependencies(task)
        elif isinstance(tasks, list):
            for task in tasks:
                self._register_run_dependencies(task)
        elif isinstance(tasks, BaseTask):
            self._run_dependencies_tasks.append(tasks)

    def _generate_run_task_futures(
        self, completion_targets: Union[Any]
    ) -> Union[List[Any], Dict[Any, Any], RunTaskFuture, Any]:
        if isinstance(completion_targets, dict):
            return {
                key: self._generate_run_task_futures(task)
                for key, task in completion_targets.items()
            }
        elif isinstance(completion_targets, list):
            return [
                self._generate_run_task_futures(task) for task in completion_targets
            ]
        elif isinstance(completion_targets, PickleTarget):
            return RunTaskFuture(completion_targets)
        else:
            return completion_targets

    def return_object(self, object: Any):
        """Returns the object to the calling task. The object needs to be pickleable"""
        if self._task_state == TaskState.RUN:
            if self._registered_return_target is None:
                self._registered_return_target = object
            else:
                raise Exception(f"return target already used")
        else:
            raise WrongTaskStateException(self._task_state, "return_target")

    def get_result(self) -> Any:
        """
        Returns the return value of the task,
        this means the single value which was passed with return_object() during run_task().
        Note that it's safe to call this method from the client side, ignoring luigi's scheduler, as it uses
        persistent data to get the result.
        """
        if not self.output().exists():
            # Actual state might be unknown, because we might be called from the client side.
            raise WrongTaskStateException(TaskState.NONE, "get_result")
        return self.output().read()

    def __repr__(self):
        """
        Build a task representation like `MyTask(param1=1.5, param2='5')`
        """
        params = self.get_params()
        param_values = self.get_param_values(params, [], self.param_kwargs)

        # Build up task id
        repr_parts = []
        param_objs = dict(params)
        for param_name, param_value in param_values:
            if (
                param_objs[param_name].significant
                and param_objs[param_name].visibility == ParameterVisibility.PUBLIC
            ):
                repr_parts.append(
                    "{}={}".format(
                        param_name, param_objs[param_name].serialize(param_value)
                    )
                )

        task_str = "{}({})".format(self.task_id, ", ".join(repr_parts))

        return task_str

    def create_child_task_with_common_params(self, task_class, **kwargs):
        params = util.common_params(self, task_class)
        params["caller_output_path"] = self._extend_output_path()
        params["job_id"] = self.job_id
        params.update(kwargs)
        return task_class(**params)

    def create_child_task(self, task_class, **kwargs):
        params = {}
        params["caller_output_path"] = self._extend_output_path()
        params["job_id"] = self.job_id
        params.update(kwargs)
        return task_class(**params)

    def cleanup(self, success: bool):
        self.cleanup_internal(success, set())

    def cleanup_internal(self, success: bool, cleanup_checklist: Set[str]):
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

    def cleanup_child_task(self, success: bool, cleanup_checklist: Set[str]):
        if self._run_dependencies_target.exists():
            _run_dependencies_tasks_from_target = self._run_dependencies_target.read()
        else:
            _run_dependencies_tasks_from_target = []
        _run_dependencies_tasks = (
            self._run_dependencies_tasks + _run_dependencies_tasks_from_target
        )
        reversed_run_dependencies_task_list = list(_run_dependencies_tasks)
        reversed_run_dependencies_task_list.reverse()
        for task in reversed_run_dependencies_task_list:
            task.cleanup_internal(success, cleanup_checklist)

        reversed_registered_task_list = list(self._registered_tasks)
        reversed_registered_task_list.reverse()
        for task in reversed_registered_task_list:
            task.cleanup_internal(success, cleanup_checklist)

    def cleanup_task(self, success: bool):
        pass
