import contextlib
import logging
from collections.abc import Iterator
from pathlib import Path


@contextlib.contextmanager
def configure_logging(
    log_file_path: Path, log_level: str | None, use_job_specific_log_file: bool
) -> Iterator[None]:
    """Set up optional file-based logging for a task run.

    When *use_job_specific_log_file* is ``True``, a ``FileHandler`` pointing
    to *log_file_path* is attached to the root logger for the duration of the
    ``with`` block and removed afterwards.
    """
    handlers: list[logging.Handler] = []
    if use_job_specific_log_file:
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        level = getattr(logging, (log_level or "INFO").upper(), logging.INFO)
        handler = logging.FileHandler(str(log_file_path))
        handler.setLevel(level)
        logging.getLogger().addHandler(handler)
        handlers.append(handler)
    try:
        yield
    finally:
        for h in handlers:
            logging.getLogger().removeHandler(h)
