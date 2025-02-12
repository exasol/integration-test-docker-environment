class SshInfo:
    """
    key_file contains path to the file containing the private key for SSH access.
    """

    def __init__(self, user: str, key_file: str):
        self.user = user
        self.key_file = key_file
