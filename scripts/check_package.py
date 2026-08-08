"""Pre-publish checks on the built sdist and wheel.

Builds are inspected as artefacts rather than as source: what matters is what a
user actually receives from PyPI, which is not always what the repo looks like.

Run after `python -m build`, before uploading:

    python -m build --outdir dist
    python scripts/check_package.py dist

Requires Python 3.11+ for `tomllib`. This is a maintainer tool, not part of the
shipped package, so it is not held to the 3.10 floor the library supports.
"""

from __future__ import annotations

import glob
import json
import sys
import tarfile
import zipfile
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parent.parent

# Repo files that are for developing whispercrawler, not for using it. Shipping
# them bloats the sdist and leaks working notes into a public release.
SDIST_UNWANTED = {
    "codebase_report.md",
    "run_demo.py",
    "benchmarks.py",
    "CLAUDE.md",
    "AGENTS.md",
    ".env.example",
    "MANIFEST.in",
    "sample",
    "output.md",
}

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}{f' - {detail}' if detail else ''}")
        failures.append(label)


def main() -> int:
    dist = Path(sys.argv[1])
    wheel = glob.glob(str(dist / "*.whl"))[0]
    sdist = glob.glob(str(dist / "*.tar.gz"))[0]

    with open(ROOT / "pyproject.toml", "rb") as f:
        version = tomllib.load(f)["project"]["version"]

    wheel_names = zipfile.ZipFile(wheel).namelist()
    sdist_names = tarfile.open(sdist).getnames()
    # Strip the "whispercrawler-<version>/" prefix every sdist member carries.
    sdist_top = {n.split("/")[1] for n in sdist_names if len(n.split("/")) > 1}

    print("version consistency")
    server = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    check(server["version"] == version, "server.json version", f"{server['version']} != {version}")
    for pkg in server["packages"]:
        if "version" in pkg:
            check(
                pkg["version"] == version,
                f"server.json packages[{pkg['registryType']}] version",
                f"{pkg['version']} != {version}",
            )

    print("wheel contents")
    check(not [n for n in wheel_names if "/tests/" in n], "no tests in wheel")
    check(not [n for n in wheel_names if n.endswith((".db", ".db-shm", ".db-wal"))], "no databases")
    check("whispercrawler/py.typed" in wheel_names, "py.typed marker present")

    print("sdist contents")
    stowaways = sorted(SDIST_UNWANTED & sdist_top)
    check(not stowaways, "no development clutter in sdist", ", ".join(stowaways))
    check(not [n for n in sdist_names if n.endswith((".db", ".db-shm", ".db-wal"))], "no databases")

    print("stale config")
    check(not (ROOT / "MANIFEST.in").exists(), "MANIFEST.in removed (hatchling ignores it)")
    check(not (ROOT / ".env.example").exists(), ".env.example removed (no env vars are read)")

    print()
    if failures:
        print(f"{len(failures)} check(s) failed")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
