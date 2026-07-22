"""
Type definitions for type checking purposes.
"""

from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Dict,
    Generator,
    Generic,
    Iterable,
    Iterator,
    List,
    Literal,
    Mapping,
    Optional,
    Pattern,
    Protocol,
    Sequence,
    Set,
    SupportsIndex,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
)
from typing_extensions import Self, TypeAlias, TypedDict, Unpack

# Proxy can be a string URL or a dict (Playwright format: {"server": "...", "username": "...", "password": "..."})
ProxyType = Union[str, dict[str, str]]
SUPPORTED_HTTP_METHODS = Literal["GET", "POST", "PUT", "DELETE"]
SelectorWaitStates = Literal["attached", "detached", "hidden", "visible"]
PageLoadStates = Literal["commit", "domcontentloaded", "load", "networkidle"]
extraction_types = Literal["text", "html", "markdown"]
StrOrBytes = Union[str, bytes]


# Copied from `playwright._impl._api_structures.SetCookieParam`
class SetCookieParam(TypedDict, total=False):
    name: str
    value: str
    url: str | None
    domain: str | None
    path: str | None
    expires: float | None
    httpOnly: bool | None
    secure: bool | None
    sameSite: Literal["Lax", "None", "Strict"] | None
    partitionKey: str | None


__all__ = [
    "TYPE_CHECKING",
    "Any",
    "AsyncGenerator",
    "Awaitable",
    "Callable",
    "Dict",
    "Generator",
    "Generic",
    "Iterable",
    "Iterator",
    "List",
    "Literal",
    "Mapping",
    "Optional",
    "Pattern",
    "Protocol",
    "Sequence",
    "Set",
    "SupportsIndex",
    "Tuple",
    "TypeAlias",
    "TypeVar",
    "Union",
    "cast",
    "overload",
    "Self",
    "TypedDict",
    "Unpack",
    "ProxyType",
    "SUPPORTED_HTTP_METHODS",
    "SelectorWaitStates",
    "PageLoadStates",
    "extraction_types",
    "StrOrBytes",
    "SetCookieParam",
]
