import base64
import os
import paramiko
import tempfile

import portalocker
from pathlib import Path
from string import Template
from typing import Optional


_LOCK_FILE = "$TMP/$MODULE-ssh-access.lock"
_DEFAULT_FOLDER = "$TMP/$MODULE"


def _path(template: str) -> Path:
    module_name = "integration-test-docker-environment"
    return Path(
        Template(template)
        .substitute(
            TMP=tempfile.gettempdir(),
            MODULE=module_name,
        )
    )


class SshKey:
    """This class hosts the private key for SSH access to a Docker Container
    and offers some convenience methods for writing the private or public key
    to a file or getting a string representation to write it to an
    authorized_keys file.

    The maker methods enable to either generate a new random key or to read it
    from a file, e.g. named "id_rsa".

    When creating a new instance based on a folder containing a file id_rsa
    then the maker method will read the private key from this file.

    If the folder does not contain this file then the maker method will
    generate a new random SSH key, will write the private key to this file and
    the public key to file id_rsa.pub in the same folder.

    If the folder does not exist, then the maker method will create the folder
    and continue with generating a new random key.

    ITDE uses python library ilock to guarantee that the key files are
    accessed only by a single process at a time.
    """
    def __init__(self, private_key: paramiko.RSAKey):
        self.private = private_key

    def write_private_key(self, path: str) -> 'SshKey':
        self.private.write_private_key_file(path) # uses 0o600 = user r/w
        return self

    def public_key_as_string(self, comment="") -> str:
        b64 = base64.b64encode(self.private.asbytes()).decode("ascii")
        return f"ssh-rsa {b64} {comment}"

    def write_public_key(self, path: str, comment="") -> 'SshKey':
        content = self.public_key_as_string(comment)
        with open(path, "w") as file:
            print(content, file=file)
        return self

    @classmethod
    def read_from(cls, private_key_file: Path) -> 'SshKey':
        with open(private_key_file, "r") as file:
            rsa_key = paramiko.RSAKey.from_private_key(file)
        return SshKey(rsa_key)

    @classmethod
    def generate(cls) -> 'SshKey':
        rsa_key = paramiko.RSAKey.generate(bits=4096)
        return SshKey(rsa_key)

    @classmethod
    def default_folder(cls) -> Path:
        folder = _path(_DEFAULT_FOLDER)
        # mode 0o700 = rwx permissions only for the current user
        # is required for the folder to enable to create files inside
        folder.mkdir(mode=0o700, exist_ok=True)
        return folder

    @classmethod
    def from_folder(cls, folder: Optional[Path] = None, args=None) -> 'SshKey':
        folder = folder if folder else cls.default_folder()
        priv = folder / "id_rsa"
        pub = folder / "id_rsa.pub"

        with portalocker.Lock(_path(_LOCK_FILE), 'wb', timeout=10) as fh:
            if priv.exists():
                return cls.read_from(priv)
            return (
                cls.generate()
                .write_private_key(priv)
                .write_public_key(pub)
            )
