import abc


class AbstractTaskFuture(abc.ABC):
    @abc.abstractmethod
    def get_output(self): ...
