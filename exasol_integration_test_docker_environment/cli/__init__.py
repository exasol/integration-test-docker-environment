import click


# Note: once code base is migrated to python >= 3.7, this can be replaced by a data class
class PortMapping:

    def __init__(self, host_port, container_port):
        self._host = host_port
        self._container = container_port

    @classmethod
    def from_string(cls, string):
        """Tries to crate a PortMapping from a string"""

        def clean(s):
            return s.strip()

        parts = clean(string).split(":")
        host_port, container_port = int(clean(parts[0])), int(clean(parts[1]))
        return cls(host_port, container_port)

    @property
    def host(self):
        """Gets the mapped host port"""
        return self._host

    @property
    def container(self):
        """Gets the mapped container port"""
        return self._container

    @staticmethod
    def string_format():
        return "<int>:<int>"

    def __str__(self):
        return f'host-port: {self.host}, container-port: {self.container}'

    def __repr__(self):
        return f'{type(self).__name__}(host_port={self.host}, container_port={self.container})'

    def __eq__(self, other):
        return self.host == other.host and self.container == other.container

    def __ne__(self, other):
        return not (self == other)


class PortMappingType(click.ParamType):
    name = "PortMapping"

    def convert(self, value, param, ctx):
        if isinstance(value, PortMapping):
            return value
        try:
            return PortMapping.from_string(value)
        except ValueError:
            error_msg = "{value!r} is not a valid port mapping. Expected format is: {fmt}"
            self.fail(error_msg.format(value=value, fmt=PortMapping.string_format()), param, ctx)
