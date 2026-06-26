import shlex
from collections.abc import Callable

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


def find_missing_external_image_references(
    image_info: ImageInfo, image_exists: Callable[[str], bool]
) -> list[str]:
    rendered_dockerfile = render_dockerfile_content(image_info)
    external_references = find_external_image_references(
        rendered_dockerfile, image_info
    )
    return [
        reference for reference in external_references if not image_exists(reference)
    ]


def find_external_image_references(
    rendered_dockerfile: str, image_info: ImageInfo
) -> list[str]:
    dependency_image_names = {
        dependency_info.get_target_complete_name()
        for dependency_info in (image_info.depends_on_images or {}).values()
    }
    stage_aliases: set[str] = set()
    external_references: list[str] = []
    for line in _logical_lines(rendered_dockerfile):
        if _starts_with_instruction(line, "FROM"):
            from_reference, stage_alias = _parse_from_instruction(line)
            if stage_alias is not None:
                stage_aliases.add(stage_alias)
            _append_external_reference(
                external_references,
                from_reference,
                dependency_image_names,
                stage_aliases,
            )
        elif _starts_with_instruction(line, "COPY"):
            for copy_reference in _parse_copy_from_references(line):
                _append_external_reference(
                    external_references,
                    copy_reference,
                    dependency_image_names,
                    stage_aliases,
                )
    return external_references


def _logical_lines(rendered_dockerfile: str) -> list[str]:
    lines: list[str] = []
    current_line = ""
    for raw_line in rendered_dockerfile.splitlines():
        line_without_comment = raw_line.split("#", 1)[0].rstrip()
        if not line_without_comment and not current_line:
            continue
        if line_without_comment.endswith("\\"):
            current_line += line_without_comment[:-1].rstrip() + " "
        else:
            current_line += line_without_comment
            stripped_line = current_line.strip()
            if stripped_line:
                lines.append(stripped_line)
            current_line = ""
    if current_line.strip():
        lines.append(current_line.strip())
    return lines


def _starts_with_instruction(line: str, instruction: str) -> bool:
    return line.upper().startswith(f"{instruction} ")


def _parse_from_instruction(line: str) -> tuple[str, str | None]:
    tokens = shlex.split(line)
    reference_index = 1
    while reference_index < len(tokens) and tokens[reference_index].startswith("--"):
        reference_index += 1
    if reference_index >= len(tokens):
        raise ValueError(f"Invalid FROM instruction: {line}")
    reference = tokens[reference_index]
    stage_alias = None
    if (
        reference_index + 2 < len(tokens)
        and tokens[reference_index + 1].upper() == "AS"
    ):
        stage_alias = tokens[reference_index + 2]
    return reference, stage_alias


def _parse_copy_from_references(line: str) -> list[str]:
    tokens = shlex.split(line)
    references: list[str] = []
    for index, token in enumerate(tokens[1:], start=1):
        if token.startswith("--from="):
            references.append(token.split("=", 1)[1])
        elif token == "--from" and index + 1 < len(tokens):
            references.append(tokens[index + 1])
    return references


def _append_external_reference(
    external_references: list[str],
    reference: str,
    dependency_image_names: set[str],
    stage_aliases: set[str],
) -> None:
    if _is_internal_reference(reference, dependency_image_names, stage_aliases):
        return
    if reference not in external_references:
        external_references.append(reference)


def _is_internal_reference(
    reference: str, dependency_image_names: set[str], stage_aliases: set[str]
) -> bool:
    return (
        reference == "scratch"
        or reference.isdigit()
        or reference in dependency_image_names
        or reference in stage_aliases
    )
