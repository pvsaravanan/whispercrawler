"""Guards on dependency ranges that exist for compatibility reasons.

A range that was narrowed to dodge a specific upstream break is easy to widen
again during a routine dependency bump, because nothing in the code references
it. These tests make the constraint fail loudly instead.
"""

from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.version import Version

# `tomllib` is stdlib only from 3.11, and the project still supports 3.10. The
# constraint is identical on every interpreter, so checking it on the newer ones
# is enough - no need to pull in a `tomli` backport just for this.
tomllib = pytest.importorskip("tomllib", reason="tomllib requires Python 3.11+")

PYPROJECT = Path(__file__).resolve().parents[3] / "pyproject.toml"

# Playwright 1.60.0 reads `pageError.location.url` unguarded in its Node driver.
# Camoufox's Firefox 135 sends a pageError with no `location`, so the driver dies
# and takes the fetch with it - on any page carrying an uncaught JS error.
FIRST_BROKEN_PLAYWRIGHT = Version("1.60.0")


@pytest.fixture(scope="module")
def fetcher_requirements() -> dict[str, Requirement]:
    with open(PYPROJECT, "rb") as f:
        pyproject = tomllib.load(f)

    extras = pyproject["project"]["optional-dependencies"]["fetchers"]
    return {(r := Requirement(spec)).name: r for spec in extras}


def test_playwright_excludes_camoufox_breaking_releases(fetcher_requirements):
    """Playwright must stay below the release that breaks ShadowFetcher."""
    playwright = fetcher_requirements["playwright"]

    assert not playwright.specifier.contains(FIRST_BROKEN_PLAYWRIGHT), (
        f"playwright{playwright.specifier} admits {FIRST_BROKEN_PLAYWRIGHT}, which crashes "
        "the Node driver on any page with an uncaught JS error, breaking ShadowFetcher"
    )


def test_playwright_still_allows_last_known_good(fetcher_requirements):
    """The upper bound must not be so tight it excludes the version we verified."""
    playwright = fetcher_requirements["playwright"]

    assert playwright.specifier.contains(Version("1.59.0")), (
        f"playwright{playwright.specifier} excludes 1.59.0, the newest release verified "
        "to work with Camoufox"
    )
