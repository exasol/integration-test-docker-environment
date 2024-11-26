import contextlib
import getpass
import json
import logging
import os
import warnings
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
)

import luigi
import networkx
from luigi.parameter import UnconsumedParameterWarning
from luigi.setup_logging import InterfaceLogging
from networkx import DiGraph

from exasol_integration_test_docker_environment.lib import (
    extract_modulename_for_build_steps,
)
from exasol_integration_test_docker_environment.lib.api.api_errors import (
    TaskFailures,
    TaskRuntimeError,
)
from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import (
    DependencyLoggerBaseTask,
)
from exasol_integration_test_docker_environment.lib.base.luigi_log_config import (
    get_log_path,
    get_luigi_log_config,
)
from exasol_integration_test_docker_environment.lib.base.task_dependency import (
    DependencyState,
    TaskDependency,
)


class JobCounterSingleton:
    """
    We use here a Singleton to avoid an unprotected global variable.
    However, this counter needs to be global counter to guarantee unique job ids.
    This is needed in case of task that finish in less than a second, to avoid duplicated job ids
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._counter = 0
        return cls._instance

    def get_next_value(self) -> int:
        # self._counter is a class variable and because of this we need to suppress type checks
        self._counter += 1  # type: ignore
        return self._counter  # type: ignore


def set_build_config(
    force_rebuild: bool,
    force_rebuild_from: Tuple[str, ...],
    force_pull: bool,
    log_build_context_content: bool,
    output_directory: str,
    temporary_base_directory: Optional[str],
    cache_directory: Optional[str],
    build_name: Optional[str],
):
    luigi.configuration.get_config().set(
        "build_config", "force_rebuild", str(force_rebuild)
    )
    luigi.configuration.get_config().set(
        "build_config", "force_rebuild_from", json.dumps(force_rebuild_from)
    )
    luigi.configuration.get_config().set("build_config", "force_pull", str(force_pull))
    set_output_directory(output_directory)
    if temporary_base_directory is not None:
        luigi.configuration.get_config().set(
            "build_config", "temporary_base_directory", temporary_base_directory
        )
    if cache_directory is not None:
        luigi.configuration.get_config().set(
            "build_config", "cache_directory", cache_directory
        )
    if build_name is not None:
        luigi.configuration.get_config().set("build_config", "build_name", build_name)
    luigi.configuration.get_config().set(
        "build_config", "log_build_context_content", str(log_build_context_content)
    )


def set_output_directory(output_directory):
    if output_directory is not None:
        luigi.configuration.get_config().set(
            "build_config", "output_directory", output_directory
        )


def set_docker_repository_config(
    docker_password: Optional[str],
    docker_repository_name: Optional[str],
    docker_username: Optional[str],
    tag_prefix: str,
    kind: str,
):
    config_class = f"{kind}_docker_repository_config"
    luigi.configuration.get_config().set(config_class, "tag_prefix", tag_prefix)
    if docker_repository_name is not None:
        luigi.configuration.get_config().set(
            config_class, "repository_name", docker_repository_name
        )
    password_environment_variable_name = f"{kind.upper()}_DOCKER_PASSWORD"
    if docker_username is not None:
        luigi.configuration.get_config().set(config_class, "username", docker_username)
        if docker_password is not None:
            luigi.configuration.get_config().set(
                config_class, "password", docker_password
            )
        elif password_environment_variable_name in os.environ:
            print(
                f"Using password from environment variable {password_environment_variable_name}"
            )
            password = os.environ[password_environment_variable_name]
            luigi.configuration.get_config().set(config_class, "password", password)
        else:
            password = getpass.getpass(
                f"{kind.capitalize()} Docker Registry Password for User %s:"
                % docker_username
            )
            luigi.configuration.get_config().set(config_class, "password", password)


def import_build_steps(flavor_path: Tuple[str, ...]):
    # We need to load the build steps of a flavor in the commandline processor,
    # because the imported classes need to be available in all processes spawned by luigi.
    # If we  import the build steps in a Luigi Task they are only available in the worker
    # which executes this task. The build method with local scheduler of luigi uses fork
    # to create the scheduler and worker processes, such that the imported classes available
    # in the scheduler and worker processes
    import importlib.util

    for path in flavor_path:
        path_to_build_steps = Path(path).joinpath("flavor_base/build_steps.py")
        module_name_for_build_steps = extract_modulename_for_build_steps(path)
        spec = importlib.util.spec_from_file_location(
            module_name_for_build_steps, path_to_build_steps
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)


def generate_root_task(task_class, *args, **kwargs) -> DependencyLoggerBaseTask:
    job_counter = JobCounterSingleton().get_next_value()
    strftime = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    params = {"job_id": f"{strftime}_{job_counter}_{task_class.__name__}"}
    params.update(kwargs)
    return task_class(**params)


def run_task(
    task_creator: Callable[[], DependencyLoggerBaseTask],
    workers: int = 2,
    task_dependencies_dot_file: Optional[str] = None,
    log_level: Optional[str] = None,
    use_job_specific_log_file: bool = False,
) -> Any:
    setup_worker()
    task = task_creator()
    success = False
    log_file_path = get_log_path(task.job_id)
    try:
        no_scheduling_errors = _run_task_with_logging_config(
            task, log_file_path, log_level, use_job_specific_log_file, workers
        )
        success = not task.failed_target.exists() and no_scheduling_errors
        return _handle_task_result(
            no_scheduling_errors, success, task, task_dependencies_dot_file
        )
    except BaseException as e:
        logging.error("Going to abort the task %s" % task)
        raise e
    finally:
        if use_job_specific_log_file:
            logging.info(
                f"The detailed log of the integration-test-docker-environment can be found at: {log_file_path}"
            )
        task.cleanup(success)


def _run_task_with_logging_config(
    task: DependencyLoggerBaseTask,
    log_file_path: Path,
    log_level: Optional[str],
    use_job_specific_log_file: bool,
    workers: int,
) -> bool:
    with _configure_logging(
        log_file_path, log_level, use_job_specific_log_file
    ) as run_kwargs:
        no_scheduling_errors = luigi.build(
            [task], workers=workers, local_scheduler=True, **run_kwargs
        )
        return no_scheduling_errors


def _handle_task_result(
    no_scheduling_errors: bool,
    success: bool,
    task: DependencyLoggerBaseTask,
    task_dependencies_dot_file: Optional[str],
) -> Any:
    generate_graph_from_task_dependencies(task, task_dependencies_dot_file)
    if success:
        return task.get_result()
    elif task.failed_target.exists():
        logging.error(f"Task {task} failed. failed target exists.")
        task_failures = list(task.collect_failures().keys())
        raise TaskRuntimeError(
            msg=f"Task {task} (or any of it's subtasks) failed.", inner=task_failures
        ) from TaskFailures(inner=task_failures)
    elif not no_scheduling_errors:
        logging.error(f"Task {task} failed. : luigi reported a scheduling error.")
        raise TaskRuntimeError(
            msg=f"Task {task} failed. reason: luigi reported a scheduling error."
        )


@contextlib.contextmanager
def _configure_logging(
    log_file_path: Path, log_level: Optional[str], use_job_specific_log_file: bool
) -> Iterator[Dict[str, str]]:
    with get_luigi_log_config(
        log_file_target=log_file_path,
        log_level=log_level,
        use_job_specific_log_file=use_job_specific_log_file,
    ) as luigi_config:
        no_configure_logging, run_kwargs = _configure_logging_parameter(
            log_level=log_level,
            luigi_config=luigi_config,
            use_job_specific_log_file=use_job_specific_log_file,
        )
        # We need to set InterfaceLogging._configured to false,
        # because otherwise luigi doesn't accept the new config.
        InterfaceLogging._configured = False
        luigi.configuration.get_config().set(
            "core", "no_configure_logging", str(no_configure_logging)
        )
        with warnings.catch_warnings():
            # This filter is necessary, because luigi uses the config no_configure_logging,
            # but doesn't define it, which seems to be a bug in luigi
            warnings.filterwarnings(
                action="ignore",
                category=UnconsumedParameterWarning,
                message=".*no_configure_logging.*",
            )
            yield run_kwargs


def _configure_logging_parameter(
    log_level: Optional[str], luigi_config: Path, use_job_specific_log_file: bool
) -> Tuple[bool, Dict[str, str]]:
    if use_job_specific_log_file:
        no_configure_logging = False
        run_kwargs = {"logging_conf_file": f"{luigi_config}"}
    else:
        no_configure_logging = True
        run_kwargs = {}
    return no_configure_logging, run_kwargs


def generate_graph_from_task_dependencies(
    task: DependencyLoggerBaseTask, task_dependencies_dot_file: Optional[str]
):
    if task_dependencies_dot_file is not None:
        print(f"Generate Task Dependency Graph to {task_dependencies_dot_file}")
        print()
        dependencies = collect_dependencies(task)
        g = DiGraph()
        for dependency in dependencies:
            g.add_node(
                dependency.source.formatted_id,
                label=dependency.source.formatted_representation,
            )
            g.add_node(
                dependency.target.formatted_id,
                label=dependency.target.formatted_representation,
            )
            g.add_edge(
                dependency.source.formatted_id,
                dependency.target.formatted_id,
                dependency=dependency.formatted,
                label=f'"type={dependency.type}, index={dependency.index}"',
            )
        networkx.nx_pydot.write_dot(g, task_dependencies_dot_file)


def collect_dependencies(task: DependencyLoggerBaseTask) -> Set[TaskDependency]:
    dependencies: Set[TaskDependency] = set()
    for root, directories, files in os.walk(task._get_dependencies_path_for_job()):
        for file in files:
            file_path = Path(root).joinpath(file)
            with open(file_path) as f:
                for line in f.readlines():
                    task_dependency: TaskDependency = TaskDependency.from_json(line)  # type: ignore
                    if task_dependency.state == DependencyState.requested.name:
                        dependencies.add(task_dependency)
    return dependencies


def setup_worker():
    luigi.configuration.get_config().set("worker", "wait_interval", str(0.1))
    luigi.configuration.get_config().set("worker", "wait_jitter", str(0.5))


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options


def cli_function(func):
    """Decorator: Register a function as having a cli equivalent"""
    func.__cli_function__ = True
    return func


def no_cli_function(func):
    """Decorator: Register a function as noy having a cli equivalent"""
    func.__cli_function__ = False
    return func
