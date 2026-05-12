from test.integration.base_task.ray_tasks import RayTaskWithReturn

from exasol_integration_test_docker_environment.lib.base.ray_run_task import (
    generate_root_task,
    run_task,
)


def test_return_value() -> None:
    """
    Integration test that verifies the Ray-style return value processing.
    """

    task_creator = lambda: generate_root_task(task_class=RayTaskWithReturn, x="Test")

    return_value = run_task(task_creator, workers=5, task_dependencies_dot_file=None)
    assert return_value == "Test-123"
