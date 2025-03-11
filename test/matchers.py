import re


class regex_matcher:
    """Assert that a given string meets some expectations."""

    def __init__(self, pattern: str, flags=0) -> None:
        self._regex = re.compile(pattern, flags)

    def __eq__(self, actual: object) -> bool:
        assert isinstance(actual, str)
        return bool(self._regex.match(actual))

    def __repr__(self) -> str:
        return self._regex.pattern
