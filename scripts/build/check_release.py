import os
import re
from pathlib import Path

from git import Repo
import toml


def get_git_version():
    repo = Repo()
    assert not repo.bare
    tag_strings = [t.name for t in repo.tags]
    tag_strings.sort(reverse=True)

    latest_tag = tag_strings[0].strip()
    assert len(latest_tag) > 0
    return latest_tag


def get_poetry_version():
    parsed_toml = toml.load('pyproject.toml')
    return parsed_toml["tool"]["poetry"]["version"].strip()


def get_change_log_version():
    with open(os.path.join(Path(__file__).resolve().parent, "..", "..", "doc", "changes", "changelog.md")) as changelog:
        changelog_str = changelog.read()
        # Search for the FIRST pattern like: "* [0.5.0](changes_0.5.0.md)" in the changelog file.
        # Note that we encapsulate the [(0.5.0)] with parenthesis, which tells re to return the matching string as group
        version_match = re.search(r"\* \[([0-9]+.[0-9]+.[0-9]+)]\(\S+\)", changelog_str)
        return version_match.groups()[0]


if __name__ == '__main__':
    poetry_version = get_poetry_version()
    latest_tag = get_git_version()
    changelog_version = get_change_log_version()
    print(f'Changelog version: "{changelog_version}"')
    print(f'Current version: "{poetry_version}"')
    print(f'Latest git tag: "{latest_tag}"')

    # We expect that the current version in pyproject.toml is alway greater than the latest tag.
    # Thus we avoid creating a release without having the version number updated.
    if poetry_version == latest_tag:
        raise ValueError("Poetry version needs to be updated!")

    if changelog_version != poetry_version:
        raise ValueError("Poetry version differs from Changelog version!")

    print("Everything looks good")
