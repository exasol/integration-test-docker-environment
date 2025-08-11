def cli_function(func):
    """Decorator: Register a function as having a cli equivalent"""
    func.__cli_function__ = True
    return func


def no_cli_function(func):
    """Decorator: Register a function as not having a cli equivalent"""
    func.__cli_function__ = False
    return func
