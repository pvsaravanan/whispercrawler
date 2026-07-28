from ._utils import (
    __CONSECUTIVE_SPACES_REGEX__,
    _is_iterable,
    _StorageTools,
    clean_spaces,
    flatten,
    html_forbidden,
    log,
    reset_logger,
    set_logger,
)

# Declared explicitly so these count as public re-exports: without `__all__`,
# strict type checking rejects `from whispercrawler.core.utils import log`.
__all__ = [
    "__CONSECUTIVE_SPACES_REGEX__",
    "_StorageTools",
    "_is_iterable",
    "clean_spaces",
    "flatten",
    "html_forbidden",
    "log",
    "reset_logger",
    "set_logger",
]
