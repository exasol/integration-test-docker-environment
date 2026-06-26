import argparse
import re
import shutil
from argparse import ArgumentParser
from pathlib import Path

import nox
import PyInstaller.__main__

from noxconfig import PROJECT_CONFIG

ROOT = Path(__file__).parent

# imports all nox task provided by the toolbox
from exasol.toolbox.nox.tasks import *  # type: ignore

# default actions to be run if nothing is explicitly specified with the -s option
nox.options.sessions = ["format:fix"]


def _validate_db_version(db_version: str, valid_db_versions: list[str], parser):
    if db_version not in valid_db_versions:
        parser.error(f"db-version must be one of {valid_db_versions}")


def parse_test_arguments(session: nox.Session):
    parser = ArgumentParser(
        usage=f"nox -s {session.name} -- [--db-version DB_VERSION] -- --test-target TEST_TARGET"
    )
    parser.add_argument("--db-version", default="default")
    parser.add_argument("--test-target", required=True, help="Pytest path to execute")
    args = parser.parse_args(session.posargs)
    _validate_db_version(args.db_version, PROJECT_CONFIG.db_versions, parser)
    return args.db_version, args.test_target


def parse_gpu_test_arguments(session: nox.Session) -> str:
    parser = ArgumentParser(usage=f"nox -s {session.name} -- [--db-version DB_VERSION]")
    parser.add_argument("--db-version", default="default")
    args = parser.parse_args(session.posargs)
    _validate_db_version(args.db_version, PROJECT_CONFIG.db_versions_gpu_only, parser)
    return args.db_version


def get_default_db_version(file_name: Path) -> str:
    with open(file_name) as txt_file:
        file_content = txt_file.read()
        pattern = r"LATEST_DB_VERSION\s*=\s*\"\"\"(\d{4}\.\d+\.\d+)\"\"\""
        match = re.search(pattern, file_content)
        return match.group(1) if match else ""


def replace_string_in_file(
    file_name: Path, old_string: str, str_to_replace: str
) -> bool:
    file_name.is_file() and bool(old_string) and bool(str_to_replace)
    file_content = file_name.read_text()
    updated_text = file_content.replace(old_string, str_to_replace)
    with open(file_name, "w") as txt_file:
        txt_file.write(updated_text)
    return True


@nox.session(name="run-integration-tests", python=False)
def run_integration_tests(session: nox.Session):
    """
    Run the selected non-GPU integration test target for the given Exasol version.
    """
    db_version, test_target = parse_test_arguments(session)
    valid_targets = set(PROJECT_CONFIG.integration_test_targets) | set(
        PROJECT_CONFIG.minimal_integration_test_targets
    )
    if test_target not in valid_targets:
        session.error(f"test-target must be one of {sorted(valid_targets)}")
    env = {"EXASOL_VERSION": db_version}
    session.run("pytest", "-m", "not gpu", test_target, env=env)


@nox.session(name="run-gpu-tests", python=False)
def run_gpu_tests(session: nox.Session):
    """
    Run the GPU integration tests for the given Exasol version.
    """
    db_version = parse_gpu_test_arguments(session)
    env = {"EXASOL_VERSION": db_version}
    session.run("pytest", "-m", "gpu", "./test/integration", env=env)


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


@nox.session(name="update-default-db-version", python=False)
def update_default_db_version(session: nox.Session):
    is_ok = True
    p = ArgumentParser(
        usage='nox -s update-default-db-version -- --version "major.minor.patch"',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--version")
    args = p.parse_args(session.posargs)
    new_version = args.version

    # Get default db version from python file
    file_name = (
        ROOT
        / "exasol_integration_test_docker_environment"
        / "cli"
        / "options"
        / "test_environment_options.py"
    )
    default_db_ver = get_default_db_version(file_name)
    is_ok = is_ok and bool(default_db_ver)
    is_ok = is_ok and replace_string_in_file(file_name, default_db_ver, new_version)

    file_name = ROOT / "doc" / "user_guide/user_guide.rst"
    is_ok = is_ok and replace_string_in_file(file_name, default_db_ver, new_version)
    print("Successfully updated" if is_ok else "Failed updating")


@nox.session(name="build-standalone-binary", python=False)
def build_standalone_binary(session: nox.Session):
    script_path = str(ROOT / "exasol_integration_test_docker_environment" / "main.py")

    p = ArgumentParser(
        usage='nox -s build-standalone-binary -- --executable-name "itde_os_x86-64"',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--executable-name")
    p.add_argument("--cleanup", action="store_true", help="Remove temporary files")
    args = p.parse_args(session.posargs)

    exe_name = getattr(args, "executable_name")

    if bool(exe_name):
        options = [
            script_path,
            "--onefile",  # As a single exe file
            f"--name={exe_name}",  # Name of the executable
            "--collect-datas=exasol_integration_test_docker_environment.templates",
            "--collect-datas=exasol_integration_test_docker_environment.docker_db_config",
            "--collect-datas=exasol_integration_test_docker_environment.certificate_resources",
        ]
        PyInstaller.__main__.run(options)
        print(f"PyInstaller completed building {exe_name}")
    else:
        print("PyInstaller needs a valid executable-name")

    if args.cleanup:
        spec_file_path = Path() / f"{exe_name}.spec"
        if spec_file_path.exists():
            spec_file_path.unlink()
        else:
            session.warn(f"Expected spec file '{spec_file_path}' doesn't exist")
        build_path = ROOT / "build" / exe_name
        if build_path.exists():
            shutil.rmtree(str(build_path))
        else:
            session.warn(f"Expected temporary build path '{build_path}' doesn't exist")


@nox.session(name="execute-itde", python=False)
def execute_itde(session: nox.Session):
    p = ArgumentParser(
        usage='nox -s execute-itde -- --executable-name "dist/itde_os_x86-64"',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--executable-name")
    args = p.parse_args(session.posargs)
    exe_name = getattr(args, "executable_name")
    session.run(f"{exe_name}", "--help")
    session.run(
        f"{exe_name}", "spawn-test-environment", "--environment-name", "test_01"
    )
