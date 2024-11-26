import base64
import os
import tempfile
from pathlib import Path
from string import Template
from typing import (
    Optional,
    Union,
)

import paramiko
import portalocker

_LOCK_FILE = "$TMP/$MODULE-ssh-access.lock"
_DEFAULT_CACHE_DIR = "$HOME/.cache/exasol/$MODULE"


def _path(template: str) -> Path:
    return Path(
        Template(template).substitute(
            TMP=tempfile.gettempdir(),
            HOME=os.path.expanduser("~"),
            MODULE="itde",
        )
    )


class SshKeyCache:
    def __init__(self, directory: Optional[Path] = None):
        self._directory = directory if directory else _path(_DEFAULT_CACHE_DIR)

    @property
    def directory(self) -> Path:
        return self._directory

    @property
    def private_key(self) -> Path:
        return self._directory / "id_rsa"

    @property
    def public_key(self) -> Path:
        return self._directory / "id_rsa.pub"


class SshKey:
    """This class hosts the private key for SSH access to a Docker Container
    and offers some convenience methods for writing the private or public key
    to a file or getting a string representation to write it to an
    authorized_keys file.

    The maker methods enable to either generate a new random key or to read it
    from a file, e.g. named "id_rsa".

    When creating a new instance based on a directory containing a file id_rsa
    then the maker method will read the private key from this file.

    If the directory does not contain this file then the maker method will
    generate a new random SSH key, will write the private key to this file and
    the public key to file id_rsa.pub in the same directory.

    If the directory does not exist, then the maker method will create the directory
    and continue with generating a new random key.

    ITDE uses python library portalocker to guarantee that the key files are
    accessed only by a single process at a time.
    """

    def __init__(self, private_key: paramiko.RSAKey):
        self.private = private_key

    def write_private_key(self, path: str) -> "SshKey":
        self.private.write_private_key_file(path)  # uses 0o600 = user r/w
        return self

    def public_key_as_string(self, comment="") -> str:
        b64 = base64.b64encode(self.private.asbytes()).decode("ascii")
        return f"ssh-rsa {b64} {comment}"

    def write_public_key(self, path: str, comment="") -> "SshKey":
        def opener(path, flags):
            return os.open(path, flags, 0o600)

        content = self.public_key_as_string(comment)
        # Windows does not support kwarg mode=0o600 here
        with open(path, "w", opener=opener) as file:
            print(content, file=file)
        return self

    @classmethod
    def read_from(cls, private_key_file: Union[Path, str]) -> "SshKey":
        with open(private_key_file) as file:
            rsa_key = paramiko.RSAKey.from_private_key(file)
        return SshKey(rsa_key)

    @classmethod
    def generate(cls) -> "SshKey":
        rsa_key = paramiko.RSAKey.generate(bits=4096)
        return SshKey(rsa_key)

    @classmethod
    def from_cache(cls, cache_directory: Optional[Path] = None) -> "SshKey":
        cache = SshKeyCache(cache_directory)
        priv = cache.private_key
        with portalocker.Lock(_path(_LOCK_FILE), "wb", timeout=10) as fh:
            if priv.exists():
                return cls.read_from(priv)
            # mode 0o700 = rwx permissions only for the current user
            # is required for the directory to enable to create files inside
            os.makedirs(cache.directory, mode=0o700, exist_ok=True)
            return (
                cls.generate()
                .write_private_key(str(priv))
                .write_public_key(str(cache.public_key))
            )
