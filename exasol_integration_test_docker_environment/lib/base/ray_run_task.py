from __future__ import annotations

import pickle
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import ray

from exasol_integration_test_docker_environment.lib.base.ray_base_task import (
    RayBaseTask,
)
from exasol_integration_test_docker_environment.lib.models.config.build_config import (
    build_config,
    set_build_config,
)
from exasol_integration_test_docker_environment.lib.utils.job_counter_singleton import (
    JobCounterSingleton,
)


def generate_root_task(task_class, *args, **kwargs) -> RayBaseTask:
    job_counter = JobCounterSingleton().get_next_value()
    strftime = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    params = {"job_id": f"{strftime}_{job_counter}_{task_class.__name__}"}
    params.update(kwargs)
    return task_class(**params)


def run_task(
    task_creator: Callable[[], RayBaseTask],
    workers: int = 2,
    task_dependencies_dot_file: str | None = None,
    log_level: str | None = None,
    use_job_specific_log_file: bool = False,
) -> Any:
    del task_dependencies_dot_file, log_level, use_job_specific_log_file
    _ensure_ray_started(workers)
    build_config_data = _capture_build_config()
    task = task_creator()
    executed_tasks: set[str] = set()
    _execute_requires(task, executed_tasks, build_config_data)
    _drive_task(task, executed_tasks, build_config_data)
    return task.get_result()


def _ensure_ray_started(workers: int) -> None:
    if not ray.is_initialized():
        ray.init(
            num_cpus=workers,
            ignore_reinit_error=True,
            include_dashboard=False,
            log_to_driver=False,
            runtime_env={"working_dir": str(Path.cwd())},
        )


@ray.remote
def _execute_task_remote(
    task_payload: bytes, build_config_data: dict[str, Any]
) -> None:
    _apply_build_config(build_config_data)
    task = pickle.loads(task_payload)
    executed_tasks: set[str] = set()
    _execute_requires(task, executed_tasks, build_config_data)
    _drive_task(task, executed_tasks, build_config_data)


def _capture_build_config() -> dict[str, Any]:
    config = build_config()
    return {
        "force_rebuild": config.force_rebuild,
        "force_rebuild_from": tuple(config.force_rebuild_from),
        "force_pull": config.force_pull,
        "log_build_context_content": config.log_build_context_content,
        "output_directory": config.output_directory,
        "temporary_base_directory": config.temporary_base_directory,
        "cache_directory": config.cache_directory,
        "build_name": config.build_name,
    }


def _apply_build_config(build_config_data: dict[str, Any]) -> None:
    set_build_config(
        build_config_data["force_rebuild"],
        build_config_data["force_rebuild_from"],
        build_config_data["force_pull"],
        build_config_data["log_build_context_content"],
        build_config_data["output_directory"],
        build_config_data["temporary_base_directory"],
        build_config_data["cache_directory"],
        build_config_data["build_name"],
    )


def _execute_requires(
    task: RayBaseTask, executed_tasks: set[str], build_config_data: dict[str, Any]
) -> None:
    required_tasks = task.requires()
    if required_tasks is None:
        return
    flattened_tasks = [
        required_task
        for required_task in _flatten(required_tasks)
        if isinstance(required_task, RayBaseTask)
    ]
    if not flattened_tasks:
        return
    ray.get(
        [
            _execute_task_remote.remote(pickle.dumps(required_task), build_config_data)
            for required_task in flattened_tasks
        ]
    )
    executed_tasks.update(required_task.task_id for required_task in flattened_tasks)


def _drive_task(
    task: RayBaseTask, executed_tasks: set[str], build_config_data: dict[str, Any]
) -> None:
    task_generator = task.run()
    if task_generator is None:
        return

    sent_value = None
    while True:
        try:
            if sent_value is None:
                yielded_value = next(task_generator)
            else:
                yielded_value = task_generator.send(sent_value)
        except StopIteration:
            break
        sent_value = _resolve_yielded_value(
            yielded_value, executed_tasks, build_config_data
        )


def _resolve_yielded_value(
    value, executed_tasks: set[str], build_config_data: dict[str, Any]
):
    if isinstance(value, dict):
        resolved_items = {
            key: _resolve_yielded_value(item, executed_tasks, build_config_data)
            for key, item in value.items()
        }
        return resolved_items
    if isinstance(value, list):
        return [
            _resolve_yielded_value(item, executed_tasks, build_config_data)
            for item in value
        ]
    if isinstance(value, RayBaseTask):
        if value.task_id not in executed_tasks:
            ray.get(_execute_task_remote.remote(pickle.dumps(value), build_config_data))
            executed_tasks.add(value.task_id)
        return value.output()
    return value


def _flatten(value):
    if isinstance(value, dict):
        flattened = []
        for item in value.values():
            flattened.extend(_flatten(item))
        return flattened
    if isinstance(value, list):
        flattened = []
        for item in value:
            flattened.extend(_flatten(item))
        return flattened
    if isinstance(value, tuple):
        flattened = []
        for item in value:
            flattened.extend(_flatten(item))
        return flattened
    return [value]
