import tomllib
from exasol_integration_test_docker_environment import version


def test_module_version_matches_toml_version():
    module_version = version.__version__
    with open("pyproject.toml", "rb") as f:
        toml_data = tomllib.load(f)
    toml_version = toml_data["project"]["version"]
    assert module_version == toml_version
