from test.integration.base_task.ray_tasks import CommonParameterRootTask

from exasol_integration_test_docker_environment.lib.base.ray_run_task import (
    generate_root_task,
    run_task,
)


def test_common_parameter(luigi_output):
    """
    Test the usage of common parameters in the Ray-style task hierarchy.
    """

    task_creator = lambda: generate_root_task(
        task_class=CommonParameterRootTask, test_parameter="input"
    )
    result = run_task(task_creator, workers=1, task_dependencies_dot_file=None)
    assert result is None
