import re
import sys

def backport(importlib_res):
    """
    Make importlib.resources.files available in Python versions below
    python 3.10., see
    https://github.com/exasol/integration-test-docker-environment/pull/419
    """
    if not re.match(f"3\.1[0-9]", sys.version):
        import importlib_resources
        setattr(importlib_res, "files", importlib_resources.files)
        setattr(importlib_res, "as_file", importlib_resources.as_file)
