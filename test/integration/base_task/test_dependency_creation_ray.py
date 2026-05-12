from test.integration.base_task.ray_tasks import DependencyRootTask

from exasol_integration_test_docker_environment.lib.base.ray_run_task import (
    generate_root_task,
    run_task,
)


def test_dependency_creation(luigi_output):
    """
    Test the creation and execution of task dependencies in the Ray-style workflow.
    """
    task_creator = lambda: generate_root_task(task_class=DependencyRootTask)
    result = run_task(task_creator, workers=1, task_dependencies_dot_file=None)
    assert result is None
