# MIT License
#
# Copyright (c) 2026, Saravanan P V
#

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import TYPE_CHECKING, Any

from whispercrawler.engines._browsers._toolbelt import build_proxy_dict
from whispercrawler.engines.toolbelt.custom import BaseFetcher, Response

if TYPE_CHECKING:
    pass

logger = logging.getLogger("whispercrawler.shadow")


def _humanize_sync(page: Any) -> None:
    """Inject random mouse movements and delays for humanization."""
    viewport = page.viewport_size or {"width": 1920, "height": 1080}
    for _ in range(random.randint(2, 5)):
        x = random.randint(0, viewport["width"])
        y = random.randint(0, viewport["height"])
        page.mouse.move(x, y)
        time.sleep(random.uniform(0.05, 0.15))
    time.sleep(random.uniform(0.5, 2.0))


async def _humanize_async(page: Any) -> None:
    """Async version of humanization."""
    viewport = page.viewport_size or {"width": 1920, "height": 1080}
    for _ in range(random.randint(2, 5)):
        x = random.randint(0, viewport["width"])
        y = random.randint(0, viewport["height"])
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.05, 0.15))
    await asyncio.sleep(random.uniform(0.5, 2.0))


class ShadowFetcher(BaseFetcher):
    """A stealthy fetcher powered by Camoufox (modified Firefox).
    Bypasses advanced bot protection like Cloudflare Turnstile.
    """

    @classmethod
    def fetch(
        cls,
        url: str,
        *,
        headless: bool = True,
        humanize: bool = True,
        geoip: bool = True,
        os_randomize: bool = False,
        timeout: int = 30000,
        proxy: str | None = None,
        block_images: bool = False,
        **kwargs: Any,
    ) -> Response:
        from camoufox.sync_api import Camoufox

        camoufox_kwargs: dict[str, Any] = {
            "headless": headless,
        }

        if geoip:
            camoufox_kwargs["geoip"] = True

        if os_randomize:
            camoufox_kwargs["os"] = None

        if proxy:
            camoufox_kwargs["proxy"] = build_proxy_dict(proxy)

        with Camoufox(**camoufox_kwargs) as browser:
            page = browser.new_page()

            if block_images:
                page.route(
                    "**/*",
                    lambda route: (
                        route.abort()
                        if route.request.resource_type == "image"
                        else route.continue_()
                    ),
                )

            page.goto(url, timeout=timeout)

            try:
                page.wait_for_load_state("networkidle", timeout=timeout)
            except:
                pass

            if humanize:
                _humanize_sync(page)

            content = page.content()
            status = 200  # Camoufox might need more work to get actual status

            return Response(
                url=url,
                content=content,
                status=status,
                reason="OK",
                cookies=tuple(dict(c) for c in page.context.cookies()),
                headers={},  # TBD
                request_headers={},  # TBD
                **cls._generate_parser_arguments(),
            )

    @classmethod
    async def async_fetch(
        cls,
        url: str,
        *,
        headless: bool = True,
        humanize: bool = True,
        geoip: bool = True,
        os_randomize: bool = False,
        timeout: int = 30000,
        proxy: str | None = None,
        block_images: bool = False,
        **kwargs: Any,
    ) -> Response:
        from camoufox.async_api import AsyncCamoufox

        camoufox_kwargs: dict[str, Any] = {"headless": headless}
        if geoip:
            camoufox_kwargs["geoip"] = True
        if os_randomize:
            camoufox_kwargs["os"] = None
        if proxy:
            camoufox_kwargs["proxy"] = build_proxy_dict(proxy)

        async with AsyncCamoufox(**camoufox_kwargs) as browser:
            page = await browser.new_page()

            if block_images:

                async def _block_img(route):
                    if route.request.resource_type == "image":
                        await route.abort()
                    else:
                        await route.continue_()

                await page.route("**/*", _block_img)

            await page.goto(url, timeout=timeout)

            try:
                await page.wait_for_load_state("networkidle", timeout=timeout)
            except:
                pass

            if humanize:
                await _humanize_async(page)

            content = await page.content()

            return Response(
                url=url,
                content=content,
                status=200,
                reason="OK",
                cookies=tuple(dict(c) for c in await page.context.cookies()),
                headers={},
                request_headers={},
                **cls._generate_parser_arguments(),
            )


ShadowCrawler = ShadowFetcher
AsyncShadowCrawler = ShadowFetcher
ShadowSession = None  # TBD
AsyncShadowSession = None  # TBD
