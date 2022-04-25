import getpass
import json
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable, Tuple, Set, Optional

import luigi
import networkx
from networkx import DiGraph

from exasol_integration_test_docker_environment.lib import extract_modulename_for_build_steps
from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import DependencyLoggerBaseTask
from exasol_integration_test_docker_environment.lib.base.luigi_log_config import get_luigi_log_config
from exasol_integration_test_docker_environment.lib.base.task_dependency import TaskDependency, DependencyState


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


def set_docker_repository_config(docker_password: str, docker_repository_name: str, docker_username: str,
                                 tag_prefix: str,
                                 kind: str):
    config_class = f'{kind}_docker_repository_config'
    luigi.configuration.get_config().set(config_class, 'tag_prefix', tag_prefix)
    if docker_repository_name is not None:
        luigi.configuration.get_config().set(config_class, 'repository_name', docker_repository_name)
    password_environment_variable_name = f"{kind.upper()}_DOCKER_PASSWORD"
    if docker_username is not None:
        luigi.configuration.get_config().set(config_class, 'username', docker_username)
        if docker_password is not None:
            luigi.configuration.get_config().set(config_class, 'password', docker_password)
        elif password_environment_variable_name in os.environ:
            print(f"Using password from environment variable {password_environment_variable_name}")
            password = os.environ[password_environment_variable_name]
            luigi.configuration.get_config().set(config_class, 'password', password)
        else:
            password = getpass.getpass(f"{kind.capitalize()} Docker Registry Password for User %s:" % docker_username)
            luigi.configuration.get_config().set(config_class, 'password', password)


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
        spec = importlib.util.spec_from_file_location(module_name_for_build_steps, path_to_build_steps)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)


def generate_root_task(task_class, *args, **kwargs) -> DependencyLoggerBaseTask:
    strftime = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    params = {"job_id": f"{strftime}_{task_class.__name__}"}
    params.update(kwargs)
    return task_class(**params)


def get_log_path(task: DependencyLoggerBaseTask):
    def_log_path = Path(task.get_main_log_path()) / "main.log"
    env_log_path = os.getenv("EXA_BUILD_LOG")
    if env_log_path is not None:
        log_path = env_log_path
    else:
        log_path = def_log_path
    return log_path


def run_task(task_creator: Callable[[], DependencyLoggerBaseTask], workers: int,
             task_dependencies_dot_file: Optional[str]) \
        -> Tuple[bool, DependencyLoggerBaseTask]:
    setup_worker()
    start_time = datetime.now()
    task = task_creator()
    success = False
    try:
        with get_luigi_log_config(get_log_path(task)) as luigi_config:
            no_scheduling_errors = luigi.build([task], workers=workers,
                                               local_scheduler=True, log_level="INFO",
                                               logging_conf_file=str(luigi_config))
        success = not task.failed_target.exists() and no_scheduling_errors
        if success:
            handle_success(task, task_dependencies_dot_file, start_time)
            return True, task
        else:
            handle_failure(task, task_dependencies_dot_file, start_time)
            return False, task
    except BaseException as e:
        traceback.print_exc()
        print("Going to abort the task %s" % task)
        return False, task  # TODO return exception
    finally:
        task.cleanup(success)


def handle_failure(task: DependencyLoggerBaseTask, task_dependencies_dot_file: Optional[str], start_time: datetime):
    generate_graph_from_task_dependencies(task, task_dependencies_dot_file)
    timedelta = datetime.now() - start_time
    print("The command failed after %s s with:" % timedelta.total_seconds())
    print_task_failures(task)

def print_task_failures(task: DependencyLoggerBaseTask):
    print()
    print("Task Failures:")
    for failure in task.collect_failures().keys():
        print(failure)
    print()

def handle_success(task: DependencyLoggerBaseTask, task_dependencies_dot_file: Optional[str], start_time: datetime):
    generate_graph_from_task_dependencies(task, task_dependencies_dot_file)
    timedelta = datetime.now() - start_time
    print("The command took %s s" % timedelta.total_seconds())


def generate_graph_from_task_dependencies(task: DependencyLoggerBaseTask, task_dependencies_dot_file: Optional[str]):
    if task_dependencies_dot_file is not None:
        print(f"Generate Task Dependency Graph to {task_dependencies_dot_file}")
        print()
        dependencies = collect_dependencies(task)
        g = DiGraph()
        for dependency in dependencies:
            g.add_node(dependency.source, label=dependency.source.representation)
            g.add_node(dependency.target, label=dependency.target.representation)
            g.add_edge(dependency.source, dependency.target,
                       dependency=dependency,
                       label=f"\"type={dependency.type}, index={dependency.index}\"")
        networkx.nx_pydot.write_dot(g, task_dependencies_dot_file)


def collect_dependencies(task: DependencyLoggerBaseTask) -> Set[TaskDependency]:
    dependencies = set()
    for root, directories, files in os.walk(task._get_dependencies_path_for_job()):
        for file in files:
            file_path = Path(root).joinpath(file)
            with open(file_path) as f:
                for line in f.readlines():
                    task_dependency = TaskDependency.from_json(line)  # type: TaskDependency
                    if task_dependency.state == DependencyState.requested.name:
                        dependencies.add(task_dependency)
    return dependencies


def setup_worker():
    luigi.configuration.get_config().set('worker', 'wait_interval', str(0.1))
    luigi.configuration.get_config().set('worker', 'wait_jitter', str(0.5))


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options
