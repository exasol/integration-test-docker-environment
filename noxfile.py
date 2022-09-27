import webbrowser
from pathlib import Path
from typing import List

import nox

from exasol_integration_test_docker_environment.cli.options.test_environment_options import LATEST_DB_VERSION

ROOT = Path(__file__).parent
LOCAL_DOC = ROOT / "doc"

nox.options.sessions = []


def _build_html_doc(session: nox.Session):
    session.run("sphinx-apidoc", "-T", "-e", "-o", "api", "../exasol_integration_test_docker_environment")
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
        session.run("sgpg",
                    "--target_branch", "github-pages/main",
                    "--push_origin", "origin",
                    "--commit",
                    "--source_branch", "main",
                    "--module_path", "${StringArray[@]}",
                    env={"StringArray": ("../integration-test-docker-environment")})


@nox.session(name="commit-pages-current", python=False)
def commit_pages_current(session: nox.Session):
    """
    Generate the GitHub pages documentation for the current branch and
    commit it to the branch github-pages/<current_branch>
    """
    branch = session.run("git", "branch", "--show-current", silent=True)
    with session.chdir(ROOT):
        session.run("sgpg",
                    "--target_branch", "github-pages/" + branch[:-1],
                    "--push_origin", "origin",
                    "--commit",
                    "--module_path", "${StringArray[@]}",
                    env={"StringArray": ("../integration-test-docker-environment")})


@nox.session(name="push-pages-main", python=False)
def push_pages_main(session: nox.Session):
    """
    Generate the GitHub pages documentation for the main branch and
    pushes it to the remote branch github-pages/main
    """
    with session.chdir(ROOT):
        session.run("sgpg",
                    "--target_branch", "github-pages/main",
                    "--push",
                    "--source_branch", "main",
                    "--module_path", "${StringArray[@]}",
                    env={"StringArray": ("../integration-test-docker-environment")})


@nox.session(name="push-pages-current", python=False)
def push_pages_current(session: nox.Session):
    """
    Generate the GitHub pages documentation for the current branch and
    pushes it to the remote branch github-pages/<current_branch>
    """
    branch = session.run("git", "branch", "--show-current", silent=True)
    with session.chdir(ROOT):
        session.run("sgpg",
                    "--target-branch", "github-pages/" + branch[:-1],
                    "--push",
                    "--module-path", "${StringArray[@]}",
                    env={"StringArray": ("../integration-test-docker-environment")})


@nox.session(name="push-pages-release", python=False)
def push_pages_release(session: nox.Session):
    """Generate the GitHub pages documentation for the release and pushes it to the remote branch github-pages/main"""
    tags = session.run("git", "tag", "--sort=committerdate", silent=True)
    # get the latest tag. last element in list is empty string, so choose second to last
    tag = tags.split("\n")[-2]
    with session.chdir(ROOT):
        session.run("sgpg",
                    "--target_branch", "github-pages/main",
                    "--push_origin", "origin",
                    "--push",
                    "--source_branch", tag,
                    "--source_origin", "tags",
                    "--module_path", "${StringArray[@]}",
                    env={"StringArray": ("../integration-test-docker-environment")})


def get_db_versions() -> List[str]:
    template_path = ROOT / "docker_db_config_template"
    return [str(path.name) for path in template_path.iterdir() if path.is_dir()]


@nox.session(name="run-tests", python=False)
@nox.parametrize('db_version', get_db_versions())
def run_tests(session: nox.Session, db_version: str):
    """Run the tests in the poetry environment"""
    with session.chdir(ROOT):
        env = {"EXASOL_VERSION": db_version}
        if session.posargs:
            for test in session.posargs:
                session.run(f"python3 run python3 -u {test}", env=env)
        else:
            session.run("python3 -u -m unittest discover ./exasol_integration_test_docker_environment/test", env=env)
