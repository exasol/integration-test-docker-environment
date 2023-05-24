import base64
import os
import paramiko
import tempfile

import portalocker
from pathlib import Path
from string import Template
from typing import Optional


_LOCK_FILE = "$TMP/$MODULE-ssh-access.lock"
_DEFAULT_FOLDER = "$HOME/.cache/exasol/$MODULE"


def _path(template: str) -> Path:
    return Path(
        Template(template)
        .substitute(
            TMP=tempfile.gettempdir(),
            HOME=os.path.expanduser('~'),
            MODULE="itde",
        )
    )


class SshFiles:
    def __init__(self, folder: Optional[Path] = None):
        self._folder = folder if folder else _path(_DEFAULT_FOLDER)

    @property
    def folder(self) -> Path:
        return self._folder

    @property
    def private_key(self) -> Path:
        return self._folder / "id_rsa"

    @property
    def public_key(self) -> Path:
        return self._folder / "id_rsa.pub"

    # @property
    # def authorized_keys_folder(self) -> Path:
    #     return self._folder / "authorized_keys"
    # 
    # @property
    # def authorized_keys_file(self) -> Path:
    #     return self.authorized_keys_folder / "authorized_keys"


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

    ITDE uses python library portalocker to guarantee that the key files are
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
        with open(path, "w", mode=0o600) as file:
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
    def from_folder(cls, folder: Optional[Path] = None) -> 'SshKey':
        def makedirs(folder: Path):
            # mode 0o700 = rwx permissions only for the current user
            # is required for the folder to enable to create files inside
            os.makedirs(folder, mode=0o700, exist_ok=True)

        # def create(folder: Path):
        #     makedirs(folder)
        #     readme = folder / "README"
        #     with open(readme, "w") as f:
        #         f.write(
        #             "This folder is meant to contain file authorized_keys"
        #             " and to be mounted into the Docker Container at /root/.ssh."
        #         )

        files = SshFiles(folder)
        priv = files.private_key

        with portalocker.Lock(_path(_LOCK_FILE), 'wb', timeout=10) as fh:
            if priv.exists():
                return cls.read_from(priv)
            makedirs(files.folder)
            # create(files.authorized_keys_folder)
            return (
                cls.generate()
                .write_private_key(priv)
                .write_public_key(files.public_key)
                # .write_public_key(files.authorized_keys_file)
            )
