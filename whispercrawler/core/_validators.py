# MIT License
#
# Copyright (c) 2026, Saravanan P V
#
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the conditions of the BSD-3-Clause License are met.

"""Configuration validators using msgspec.Struct."""

from __future__ import annotations

import msgspec


class CrawlerConfig(msgspec.Struct):
    """Configuration for Crawler (static HTTP fetcher)."""

    browser_type: str = "chrome"
    http_version: int = 3
    timeout: float = 30.0
    follow_redirects: bool = True
    max_redirects: int = 10
    verify_ssl: bool = True
    proxy: str | None = None
    headers: dict = {}  # type: ignore[type-arg]
    auto_save: bool = False
    adaptive: bool = False


class GhostConfig(msgspec.Struct):
    """Configuration for GhostCrawler (Playwright/Patchright browser)."""

    headless: bool = True
    stealth: bool = True
    timeout: int = 30000
    network_idle: bool = True
    disable_resources: bool = False
    proxy: str | None = None
    cdp_url: str | None = None
    real_chrome: bool = False
    auto_save: bool = False
    adaptive: bool = False


class ShadowConfig(msgspec.Struct):
    """Configuration for ShadowCrawler (Camoufox modified Firefox)."""

    headless: bool = True
    humanize: bool = True
    geoip: bool = True
    os_randomize: bool = False
    timeout: int = 30000
    proxy: str | None = None
    block_images: bool = False
    auto_save: bool = False
    adaptive: bool = False


class StorageConfig(msgspec.Struct):
    """Configuration for WhisperStorage."""

    db_path: str = ""
    similarity_threshold: float = 0.6
    max_records_per_domain: int = 10000
