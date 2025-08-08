import argparse
import json
import os
import re
import shutil
from argparse import ArgumentParser
from enum import Enum
from pathlib import Path
from typing import List

import nox
import toml
from packaging.version import Version

from noxconfig import PROJECT_CONFIG

ROOT = Path(__file__).parent

# imports all nox task provided by the toolbox
from exasol.toolbox.nox.tasks import *  # type: ignore

# default actions to be run if nothing is explicitly specified with the -s option
nox.options.sessions = ["project:fix"]


class TestSet(Enum):
    GPU_ONLY = "gpu-only"
    DEFAULT = "default"


def parse_test_arguments(session: nox.Session):
    test_set_values = [ts.value for ts in TestSet]
    parser = ArgumentParser(
        usage=f"nox -s {session.name} -- [--db-version DB_VERSION] --test-set {{{','.join(test_set_values)}}}"
    )
    parser.add_argument("--db-version", default="default")
    parser.add_argument(
        "--test-set",
        type=TestSet,
        required=True,
        help="Test set name",
    )
    args = parser.parse_args(session.posargs)
    db_version = args.db_version
    if args.test_set == TestSet.GPU_ONLY:
        if db_version not in get_db_versions_gpu_only():
            parser.error(f"db-version must be one of {get_db_versions_gpu_only()}")
    else:
        if db_version not in get_db_versions():
            parser.error(f"db-version must be one of {get_db_versions()}")
    return db_version, args.test_set


def get_db_versions_gpu_only() -> list[str]:
    template_path = ROOT / "docker_db_config_template"
    db_versions = [str(path.name) for path in template_path.iterdir() if path.is_dir()]

    # Filter for versions later than or equal to 8.34.0
    db_versions = [
        db_version
        for db_version in db_versions
        if Version(db_version) >= Version("8.34.0")
    ]
    db_versions.append("default")
    return db_versions


def get_db_versions() -> list[str]:
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


def get_default_db_version(file_name):
    with open(file_name) as txt_file:
        file_content = txt_file.read()
        pattern = r"\s*LATEST_DB_VERSION\s*=\s*[\"']+([\d\.]+)[\"']+"
        match = re.search(pattern, file_content)
        return match.group(1) if match else None


def replace_string_in_file(file_name, old_string, str_to_replace):
    is_ok = file_name and os.path.exists(file_name) and old_string and str_to_replace
    if not is_ok:
        return False
    updated_text = ""
    with open(file_name) as txt_file:
        file_content = txt_file.read()
        updated_text = file_content.replace(old_string, str_to_replace)
    with open(file_name, "w") as txt_file:
        txt_file.write(updated_text)
    return True


@nox.session(name="run-all-tests", python=False)
def run_all_tests(session: nox.Session):
    """
    Run all tests using the specified version of Exasol database.
    If test-set is set to "default":
        This nox tasks runs 3 different groups of tests for the ITDE:
        1. new unit tests (using pytest framework)
        2. new integration tests (also using pytest), excluding GPU Tests.
        3. old tests (mainly integration tests) using python module "unitest"
    If test-set is set to "gpu-only":
        This nox tasks runs only the GPU specific integration tests using pytest.
    """
    db_version, test_set = parse_test_arguments(session)
    env = {"EXASOL_VERSION": db_version}
    if test_set == TestSet.GPU_ONLY:
        session.run("pytest", "-m", "gpu", "./test/integration", env=env)
    else:
        session.run("pytest", "./test/unit")
        session.run("pytest", "-m", "not gpu", "./test/integration", env=env)
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
def run_minimal_tests(session: nox.Session):
    """
    This nox task runs selected tests.
    There are two options: `--db-version` and `--test-set`.
    It `test-set` is set to `gpu-only`,
    then only the minimal GPU tests will be executed, using the
    specified version of Exasol database.
    Otherwise, it executes  new unit tests and selected old and new integration tests using the
    specified version of Exasol database.
    """
    db_version, test_set = parse_test_arguments(session)
    env = {"EXASOL_VERSION": db_version}
    if test_set == TestSet.GPU_ONLY:
        session.run("pytest", "-m", "gpu", "./test/integration", env=env)
    else:
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
                "base_task",
            ],
            "unit": ["./test/unit"],
        }
        session.run("pytest", *minimal_tests["unit"])
        for test in minimal_tests["new-itest"]:
            session.run(
                "pytest",
                "-m",
                "not gpu",
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

    def parser() -> ArgumentParser:
        p = ArgumentParser(
            usage="nox -s get-all-db-versions -- [--gpu-only]",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        p.add_argument("--gpu-only", action="store_true")
        return p

    args = parser().parse_args(session.posargs)
    if args.gpu_only:
        print(json.dumps(get_db_versions_gpu_only()))
    else:
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


@nox.session(name="update-default-db-version", python=False)
def update_default_db_version(session: nox.Session):
    is_ok = True
    p = ArgumentParser(
        usage="nox -s update-default-db-version -- --version \"major.minor.patch\"",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--version")
    args = p.parse_args(session.posargs)
    new_version = args.version

    # Get default db version from python file
    pwd = os.getcwd()
    file_name = os.path.join(
        pwd,
        "exasol_integration_test_docker_environment/cli/options/test_environment_options.py",
    )
    default_db_ver = get_default_db_version(file_name)
    is_ok = is_ok and default_db_ver
    is_ok = is_ok and replace_string_in_file(file_name, default_db_ver, new_version)

    file_name = os.path.join(pwd, "doc/user_guide/user_guide.rst")
    is_ok = is_ok and replace_string_in_file(file_name, default_db_ver, new_version)
    print("Successfully updated" if is_ok else "Failed updating")
