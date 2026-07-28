"""Shared test collection rules.

`pytest-httpbin` serves the local HTTP fixtures that the fetcher, CLI, and MCP
suites request. It cannot be installed alongside Playwright on Python < 3.12:
httpbin 0.10.4 pins ``greenlet<3.0`` for those versions while Playwright
requires ``greenlet>=3.1.1``, and the older httpbin 0.10.0 needs
``parse_authorization_header``, which Werkzeug removed in 2.3.

Rather than resolve that with EOL Flask/Werkzeug pins for every developer, the
dependency is declared only for Python 3.12+ (see ``pyproject.toml``) and the
modules that need it are skipped wherever it is absent. Everything that does
not touch the fixture server still runs on every supported version.
"""

from importlib.util import find_spec

_HTTPBIN_DEPENDENT = [
    "ai/test_ai_mcp.py",
    "cli/test_cli.py",
    "fetchers/async/test_dynamic.py",
    "fetchers/async/test_dynamic_session.py",
    "fetchers/async/test_requests.py",
    "fetchers/async/test_stealth.py",
    "fetchers/async/test_stealth_session.py",
    "fetchers/sync/test_dynamic.py",
    "fetchers/sync/test_requests.py",
    "fetchers/sync/test_stealth_session.py",
    "fetchers/test_impersonate_list.py",
]

collect_ignore = [] if find_spec("pytest_httpbin") else list(_HTTPBIN_DEPENDENT)
