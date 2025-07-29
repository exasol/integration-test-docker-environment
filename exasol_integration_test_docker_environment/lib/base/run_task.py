import logging
import os
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    Callable,
    Optional,
)

import luigi
import networkx
from networkx.classes import DiGraph

from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import (
    DependencyLoggerBaseTask,
)
from exasol_integration_test_docker_environment.lib.base.task_dependency import (
    DependencyState,
    TaskDependency,
)
from exasol_integration_test_docker_environment.lib.logging.configure_logging import (
    configure_logging,
)
from exasol_integration_test_docker_environment.lib.logging.luigi_log_config import (
    get_log_path,
)
from exasol_integration_test_docker_environment.lib.models.api_errors import (
    TaskFailures,
    TaskRuntimeError,
)
from exasol_integration_test_docker_environment.lib.utils.job_counter_singleton import (
    JobCounterSingleton,
)


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
    with configure_logging(
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


def collect_dependencies(task: DependencyLoggerBaseTask) -> set[TaskDependency]:
    dependencies: set[TaskDependency] = set()
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
