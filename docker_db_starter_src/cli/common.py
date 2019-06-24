import getpass
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Tuple, Set

import luigi
import networkx
from networkx import DiGraph

from docker_db_starter_src.lib.stoppable_task import StoppableTask
from docker_db_starter_src.lib.task_dependency import TaskDependency, DependencyState


def set_build_config(force_rebuild: bool,
                     force_rebuild_from: Tuple[str, ...],
                     force_pull: bool,
                     log_build_context_content: bool,
                     output_directory: str,
                     temporary_base_directory: str,
                     cache_directory: str,
                     build_name: str, ):
    luigi.configuration.get_config().set('build_config', 'force_rebuild', str(force_rebuild))
    luigi.configuration.get_config().set('build_config', 'force_rebuild_from', json.dumps(force_rebuild_from))
    luigi.configuration.get_config().set('build_config', 'force_pull', str(force_pull))
    set_output_directory(output_directory)
    if temporary_base_directory is not None:
        luigi.configuration.get_config().set('build_config', 'temporary_base_directory', temporary_base_directory)
    if cache_directory is not None:
        luigi.configuration.get_config().set('build_config', 'cache_directory', cache_directory)
    if build_name is not None:
        luigi.configuration.get_config().set('build_config', 'build_name', build_name)
    luigi.configuration.get_config().set('build_config', 'log_build_context_content', str(log_build_context_content))


def set_output_directory(output_directory):
    if output_directory is not None:
        luigi.configuration.get_config().set('build_config', 'output_directory', output_directory)


# TODO add watchdog, which uploads the logs after given ammount of time, to get logs before travis kills the job
def run_tasks(tasks_creator: Callable[[], List[luigi.Task]],
              workers: int,
              on_success: Callable[[], None] = None,
              on_failure: Callable[[], None] = None):
    setup_worker()
    start_time = datetime.now()
    tasks = remove_stoppable_task_targets(tasks_creator)
    no_scheduling_errors = luigi.build(tasks, workers=workers, local_scheduler=True, log_level="INFO")
    if StoppableTask().failed_target.exists() or not no_scheduling_errors:
        handle_failure(on_failure)
    else:
        handle_success(on_success, start_time)


def handle_success(on_success: Callable[[], None], start_time: datetime):
    if on_success is not None:
        on_success()
    timedelta = datetime.now() - start_time
    print("The command took %s s" % timedelta.total_seconds())
    exit(0)

def handle_failure(on_failure: Callable[[], None]):
    if on_failure is not None:
        on_failure()
    exit(1)


def remove_stoppable_task_targets(tasks_creator):
    stoppable_task = StoppableTask()
    if stoppable_task.failed_target.exists():
        stoppable_task.failed_target.remove()
    if stoppable_task.timers_dir.exists():
        shutil.rmtree(str(stoppable_task.timers_dir))
    if stoppable_task.dependencies_dir.exists():
        shutil.rmtree(str(stoppable_task.dependencies_dir))
    tasks = tasks_creator()
    return tasks


def setup_worker():
    luigi.configuration.get_config().set('worker', 'wait_interval', str(0.1))
    luigi.configuration.get_config().set('worker', 'wait_jitter', str(0.5))


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options
