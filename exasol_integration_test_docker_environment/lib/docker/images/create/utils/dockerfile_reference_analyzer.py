from jinja2 import Template

from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageInfo,
)


def render_dockerfile_content(image_info: ImageInfo) -> str:
    image_description = image_info.image_description
    if image_description is None:
        raise ValueError("image_info.image_description must not be None")
    with open(image_description.dockerfile) as file:
        dockerfile_content = file.read()
    template = Template(dockerfile_content)
    image_names_of_dependencies = {
        key: dependency_info.get_target_complete_name()
        for key, dependency_info in (image_info.depends_on_images or {}).items()
    }
    return template.render(**image_names_of_dependencies)
