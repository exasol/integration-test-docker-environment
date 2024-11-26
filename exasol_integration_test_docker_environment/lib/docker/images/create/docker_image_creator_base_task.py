import luigi

from exasol_integration_test_docker_environment.lib.base.docker_base_task import (
    DockerBaseTask,
)
from exasol_integration_test_docker_environment.lib.base.json_pickle_parameter import (
    JsonPickleParameter,
)
from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageInfo,
)


class DockerImageCreatorBaseTask(DockerBaseTask):
    image_name: str = luigi.Parameter()  # type: ignore
    # ParameterVisibility needs to be hidden instead of private, because otherwise a MissingParameter gets thrown
    image_info: ImageInfo = JsonPickleParameter(
        ImageInfo,
        visibility=luigi.parameter.ParameterVisibility.HIDDEN,
        significant=True,
    )  # type: ignore
