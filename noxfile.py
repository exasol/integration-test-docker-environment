import json
import shutil
from pathlib import Path
from typing import List

import nox
import toml

from noxconfig import PROJECT_CONFIG

ROOT = Path(__file__).parent

# imports all nox task provided by the toolbox
from exasol.toolbox.nox.tasks import *  # type: ignore

# default actions to be run if nothing is explicitly specified with the -s option
nox.options.sessions = ["project:fix"]


def get_db_versions() -> List[str]:
    template_path = ROOT / "docker_db_config_template"
    db_versions = [str(path.name) for path in template_path.iterdir() if path.is_dir()]
    db_versions.append("default")
    # The ITDE only supports EXAConf templates for docker-db versions in the format major.minor.bugfix.
    # If a user supplies versions with some additions, such as d1, prerelease, we filter these from the version number.
    # However, we use the templates here to generate the test matrix for GitHub Actions.
    # This means we need to adapt the list for images with special names.
    # We need to remove the version 8.17.0 for the moment, because there exist no docker-db images with that version
    # on DockerHub, yet. Instead, we add its pre-release version.
    db_versions.remove("8.17.0")
    db_versions.append("prerelease-8.17.0")
    db_versions.remove("7.1.0")
    db_versions.append("7.1.0-d1")
    return db_versions


@nox.session(name="run-all-tests", python=False)
@nox.parametrize("db_version", get_db_versions())
def run_all_tests(session: nox.Session, db_version: str):
    """
    Run all tests using the specified version of Exasol database or all versions currently supported by the ITDE.
    This nox tasks runs 3 different groups of tests for the ITDE:
    1. new unit tests (using pytest framework)
    2. new integration tests (also using pytest)
    3. old tests (mainly integration tests) using python module "unitest"
    """
    env = {"EXASOL_VERSION": db_version}
    session.run("pytest", "./test/unit")
    session.run("pytest", "./test/integration", env=env)
    with session.chdir(ROOT):
        session.run(
            "python",
            "-u",
            "-m",
            "unittest",
            "discover",
            "./exasol_integration_test_docker_environment/test",
            env=env,
        )


@nox.session(name="run-minimal-tests", python=False)
@nox.parametrize("db_version", get_db_versions())
def run_minimal_tests(session: nox.Session, db_version: str):
    """
    This nox task runs selected tests from new unit tests and selected old and new integration tests using the
    specified version of Exasol database or all versions currently supported by the ITDE.
    """
    env = {"EXASOL_VERSION": db_version}
    minimal_tests = {
        "old-itest": [
            # "test_cli_test_environment.py",
            "test_doctor.py",
            "test_termination_handler.py",
        ],
        "new-itest": [
            "test_api_test_environment.py",
            "test_cli_environment.py",
            "test_db_container_log_thread.py",
            "test_api_logging.py",
        ],
        "unit": ["./test/unit"],
    }
    session.run("pytest", *minimal_tests["unit"])
    for test in minimal_tests["new-itest"]:
        session.run(
            "pytest",
            f"./test/integration/{test}",
            env=env,
        )
    with session.chdir(ROOT):
        for test in minimal_tests["old-itest"]:
            session.run(
                "python",
                "-u",
                f"./exasol_integration_test_docker_environment/test/{test}",
                env=env,
            )


@nox.session(name="get-all-db-versions", python=False)
def get_all_db_versions(session: nox.Session):
    """Returns all, known, db-versions as JSON string"""
    print(json.dumps(get_db_versions()))


@nox.session(name="release", python=False)
def release(session: nox.Session):
    project = toml.load(ROOT / "pyproject.toml")
    version = project["tool"]["poetry"]["version"]
    session.run("git", "tag", version)
    session.run("git", "push", "origin", version)


@nox.session(name="starter-scripts-checksums", python=False)
def starter_scripts_checksums(session: nox.Session):
    start_script_dir = ROOT / "starter_scripts"
    with session.chdir(start_script_dir):
        for start_script_entry in start_script_dir.iterdir():
            if start_script_entry.is_file():
                sha512: str = session.run("sha512sum", start_script_entry.name, silent=True)  # type: ignore
                with open(
                    start_script_dir
                    / "checksums"
                    / f"{start_script_entry.name}.sha512sum",
                    "w",
                ) as f:
                    f.write(sha512)
    session.run("git", "add", "starter_scripts/checksums")


@nox.session(name="copy-docker-db-config-templates", python=False)
def copy_docker_db_config_templates(session: nox.Session):
    target_path = (
        ROOT / "exasol_integration_test_docker_environment" / "docker_db_config"
    )
    if target_path.is_dir():
        shutil.rmtree(target_path)
    with session.chdir(ROOT):
        session.run("cp", "-rL", "docker_db_config_template", str(target_path))
    session.run("git", "add", str(target_path))


@nox.session(name="test:unit", python=False)
def itde_unit_tests(session: nox.Session) -> None:
    """Runs all unit tests"""
    from exasol.toolbox.nox._shared import _context
    from exasol.toolbox.nox._test import _unit_tests

    context = _context(session, coverage=True)
    _unit_tests(session, PROJECT_CONFIG, context)
