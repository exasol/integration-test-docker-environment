from git import Repo
import toml

repo = Repo()
assert not repo.bare
tag_strings = [t.name for t in repo.tags]
tag_strings.sort(reverse=True)

latest_tag = tag_strings[0].strip()
assert len(latest_tag) > 0

parsed_toml = toml.load('pyproject.toml')
poetry_version = parsed_toml["tool"]["poetry"]["version"].strip()
print(f'Current version: "{poetry_version}"')
print(f'Latest git tag: "{latest_tag}"')

# We expect that the current version in pyproject.toml is alway greater than the latest tag.
# Thus we avoid creating a release without having the version number updated.
if poetry_version == latest_tag:
    raise ValueError("Poetry version needs to be updated!")
