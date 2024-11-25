from typing import (
    Optional,
    Tuple,
)

from exasol_integration_test_docker_environment.cli.options.docker_repository_options import (
    DEFAULT_DOCKER_REPOSITORY_NAME,
)
from exasol_integration_test_docker_environment.cli.options.system_options import (
    DEFAULT_OUTPUT_DIRECTORY,
)
from exasol_integration_test_docker_environment.lib.api.common import (
    generate_root_task,
    no_cli_function,
    run_task,
    set_build_config,
    set_docker_repository_config,
)
from exasol_integration_test_docker_environment.lib.data.test_container_content_description import (
    TestContainerContentDescription,
)
from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageInfo,
)
from exasol_integration_test_docker_environment.lib.test_environment.analyze_test_container import (
    AnalyzeTestContainer,
    DockerTestContainerPush,
)


@no_cli_function
def push_test_container(
    test_container_content: TestContainerContentDescription,
    force_push: bool = False,
    push_all: bool = False,
    force_rebuild: bool = False,
    force_rebuild_from: Tuple[str, ...] = tuple(),
    force_pull: bool = False,
    output_directory: str = DEFAULT_OUTPUT_DIRECTORY,
    temporary_base_directory: str = "/tmp",
    log_build_context_content: bool = False,
    cache_directory: Optional[str] = None,
    build_name: Optional[str] = None,
    source_docker_repository_name: str = DEFAULT_DOCKER_REPOSITORY_NAME,
    source_docker_tag_prefix: str = "",
    source_docker_username: Optional[str] = None,
    source_docker_password: Optional[str] = None,
    target_docker_repository_name: str = DEFAULT_DOCKER_REPOSITORY_NAME,
    target_docker_tag_prefix: str = "",
    target_docker_username: Optional[str] = None,
    target_docker_password: Optional[str] = None,
    workers: int = 5,
    task_dependencies_dot_file: Optional[str] = None,
    log_level: Optional[str] = None,
    use_job_specific_log_file: bool = False,
) -> ImageInfo:
    """
    This function pushes all stages of the test container for the test environment.
    If the stages do not exist locally, the system will build or pull them before the push.
    """
    set_build_config(
        force_rebuild,
        force_rebuild_from,
        force_pull,
        log_build_context_content,
        output_directory,
        temporary_base_directory,
        cache_directory,
        build_name,
    )
    # Use AnalyzeTestContainer to ensure that all luigi processes got it loaded
    analyze_task = AnalyzeTestContainer.__class__.__name__

    set_docker_repository_config(
        source_docker_password,
        source_docker_repository_name,
        source_docker_username,
        source_docker_tag_prefix,
        "source",
    )
    set_docker_repository_config(
        target_docker_password,
        target_docker_repository_name,
        target_docker_username,
        target_docker_tag_prefix,
        "target",
    )
    task_creator = lambda: generate_root_task(
        task_class=DockerTestContainerPush,
        test_container_content=test_container_content,
        force_push=force_push,
        push_all=push_all,
    )
    image_infos = run_task(
        task_creator,
        workers,
        task_dependencies_dot_file,
        log_level=log_level,
        use_job_specific_log_file=use_job_specific_log_file,
    )
    return image_infos[0]
