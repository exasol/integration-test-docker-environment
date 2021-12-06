import subprocess

import pkg_resources

from jinja2 import Template


def create_certificate(host_name: str, certificate_dir: str) -> None:
    template_str = pkg_resources.resource_string(
        "exasol_integration_test_docker_environment",
        "create_certificate.sh")  # type: bytes
    template = Template(template_str.decode("utf-8"))
    rendered_template = template.render(HOST_NAME=host_name,
                                        cert_dir=certificate_dir)

    result = subprocess.run(rendered_template, stdout=subprocess.PIPE, shell=True)
    result.check_returncode()
