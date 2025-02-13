class JobCounterSingleton:
    """
    We use here a Singleton to avoid an unprotected global variable.
    However, this counter needs to be global counter to guarantee unique job ids.
    This is needed in case of task that finish in less than a second, to avoid duplicated job ids
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._counter = 0
        return cls._instance

    def get_next_value(self) -> int:
        # self._counter is a class variable and because of this we need to suppress type checks
        self._counter += 1  # type: ignore
        return self._counter  # type: ignore
