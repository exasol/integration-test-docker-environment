import toml
import json
import webbrowser
from pathlib import Path
from typing import List

import nox

ROOT = Path(__file__).parent
LOCAL_DOC = ROOT / "doc"

nox.options.sessions = []


def _build_html_doc(session: nox.Session):
    session.run(
        "sphinx-apidoc",
        "-T",
        "-e",
        "-o",
        "api",
        "../exasol_integration_test_docker_environment",
    )
    session.run("sphinx-build", "-b", "html", "-W", ".", ".build-docu")


def _open_docs_in_browser(session: nox.Session):
    index_file_path = Path(".build-docu/index.html").resolve()
    webbrowser.open_new_tab(index_file_path.as_uri())


@nox.session(name="build-html-doc", python=False)
def build_html_doc(session: nox.Session):
    """Build the documentation for current checkout"""
    with session.chdir(LOCAL_DOC):
        _build_html_doc(session)


@nox.session(name="open-html-doc", python=False)
def open_html_doc(session: nox.Session):
    """Open the documentation for current checkout in the browser"""
    with session.chdir(LOCAL_DOC):
        _open_docs_in_browser(session)


@nox.session(name="build-and-open-html-doc", python=False)
def build_and_open_html_doc(session: nox.Session):
    """Build and open the documentation for current checkout in browser"""
    with session.chdir(LOCAL_DOC):
        _build_html_doc(session)
        _open_docs_in_browser(session)


@nox.session(name="commit-pages-main", python=False)
def commit_pages_main(session: nox.Session):
    """
    Generate the GitHub pages documentation for the main branch and
    commit it to the branch github-pages/main
    """
    with session.chdir(ROOT):
        session.run(
            "sgpg",
            "--target-branch",
            "github-pages/main",
            "--push-origin",
            "origin",
            "--commit",
            "--source-branch",
            "main",
            "--module-path",
            "../integration-test-docker-environment",
        )


@nox.session(name="commit-pages-current", python=False)
def commit_pages_current(session: nox.Session):
    """
    Generate the GitHub pages documentation for the current branch and
    commit it to the branch github-pages/<current_branch>
    """
    branch = session.run("git", "branch", "--show-current", silent=True)
    with session.chdir(ROOT):
        session.run(
            "sgpg",
            "--target-branch",
            "github-pages/" + branch[:-1],
            "--push-origin",
            "origin",
            "--commit",
            "--module-path",
            "../integration-test-docker-environment",
        )


@nox.session(name="push-pages-main", python=False)
def push_pages_main(session: nox.Session):
    """
    Generate the GitHub pages documentation for the main branch and
    pushes it to the remote branch github-pages/main
    """
    with session.chdir(ROOT):
        session.run(
            "sgpg",
            "--target-branch",
            "github-pages/main",
            "--push",
            "--source-branch",
            "main",
            "--module-path",
            "../integration-test-docker-environment",
        )


@nox.session(name="push-pages-current", python=False)
def push_pages_current(session: nox.Session):
    """
    Generate the GitHub pages documentation for the current branch and
    pushes it to the remote branch github-pages/<current_branch>
    """
    branch = session.run("git", "branch", "--show-current", silent=True)
    with session.chdir(ROOT):
        session.run(
            "sgpg",
            "--target-branch",
            "github-pages/" + branch[:-1],
            "--push",
            "--module-path",
            "../integration-test-docker-environment",
        )


@nox.session(name="push-pages-release", python=False)
def push_pages_release(session: nox.Session):
    """Generate the GitHub pages documentation for the release and pushes it to the remote branch github-pages/main"""
    tags = session.run("git", "tag", "--sort=committerdate", silent=True)
    # get the latest tag. last element in list is empty string, so choose second to last
    tag = tags.split("\n")[-2]
    with session.chdir(ROOT):
        session.run(
            "sgpg",
            "--target-branch",
            "github-pages/main",
            "--push-origin",
            "origin",
            "--push",
            "--source-branch",
            tag,
            "--source-origin",
            "tags",
            "--module-path",
            "../integration-test-docker-environment",
        )


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


@nox.session(name="run-tests", python=False)
@nox.parametrize("db_version", get_db_versions())
def run_tests(session: nox.Session, db_version: str):
    """Run the tests in the poetry environment"""
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
    """Run the minimal tests in the poetry environment"""
    env = {"EXASOL_VERSION": db_version}
    minimal_tests = {
        "old-itest": [
            "test_api_test_environment.py",
            # "test_cli_test_environment.py",
            "test_doctor.py",
            "test_termination_handler.py",
        ],
        "new-itest": [
            "test_cli_environment.py"
            ],
        "unit": "./test/unit",
    }
    session.run("pytest", minimal_tests["unit"])
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
