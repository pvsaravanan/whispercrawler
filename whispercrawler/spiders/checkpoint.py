from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

import anyio
import orjson
from anyio import Path as AsyncPath

from whispercrawler.core._types import Any, List, Optional, Set
from whispercrawler.core.utils import log
from whispercrawler.spiders.request import Request


@dataclass
class CheckpointData:
    """Container for checkpoint state."""

    requests: List["Request"] = field(default_factory=list)
    seen: Set[bytes] = field(default_factory=set)


#: Marker left in place of a value that cannot survive a JSON round-trip.
_UNSERIALIZABLE = "unserializable"


def _encode_value(value: Any) -> Any:
    """Recursively convert a request-kwargs value into a JSON-safe form.

    Anything we cannot represent (auth objects, SSL contexts, open file handles)
    is replaced with a marker rather than handed to orjson. Losing one kwarg on
    resume is recoverable; letting the serializer raise aborts the whole crawl.
    """
    if isinstance(value, bytes):
        return {"__type__": "bytes", "hex": value.hex()}
    if isinstance(value, BytesIO):
        return {"__type__": "bytesio", "hex": value.getvalue().hex()}
    if isinstance(value, tuple):
        return {"__type__": "tuple", "items": [_encode_value(v) for v in value]}
    if isinstance(value, dict):
        return {k: _encode_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_encode_value(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    log.warning(
        f"Checkpoint cannot serialize {type(value).__name__} value; "
        "it will be dropped when the crawl resumes"
    )
    return {"__type__": _UNSERIALIZABLE, "repr": repr(value)[:200]}


def _decode_value(value: Any) -> Any:
    """Reverse of `_encode_value`.

    Keys whose values were dropped at encode time are omitted entirely, so the
    request is retried without them rather than with a bogus placeholder.
    """
    if isinstance(value, dict):
        tag = value.get("__type__")
        if tag == "bytes":
            return bytes.fromhex(value["hex"])
        if tag == "bytesio":
            return BytesIO(bytes.fromhex(value["hex"]))
        if tag == "tuple":
            return tuple(_decode_value(v) for v in value["items"] if not _is_unserializable(v))
        return {k: _decode_value(v) for k, v in value.items() if not _is_unserializable(v)}
    if isinstance(value, list):
        return [_decode_value(v) for v in value if not _is_unserializable(v)]
    return value


def _is_unserializable(value: Any) -> bool:
    """True for the marker `_encode_value` leaves behind for dropped values."""
    return isinstance(value, dict) and value.get("__type__") == _UNSERIALIZABLE


def _request_to_dict(request: "Request") -> dict[str, Any]:
    """Convert a Request into a JSON-serializable dict."""
    return {
        "url": request.url,
        "sid": request.sid,
        "priority": request.priority,
        "dont_filter": request.dont_filter,
        "meta": _encode_value(request.meta),
        "_retry_count": request._retry_count,
        "callback_name": (
            getattr(request.callback, "__name__", None) if request.callback is not None else None
        ),
        "session_kwargs": _encode_value(request._session_kwargs),
    }


def _request_from_dict(data: dict[str, Any]) -> "Request":
    """Reconstruct a Request from its JSON dict form.

    The callback itself is not restored here - `_restore_callback()` looks it
    up on the spider afterwards, same as the callback is deferred after unpickling.
    """
    request = Request(
        url=data["url"],
        sid=data.get("sid", ""),
        priority=data.get("priority", 0),
        dont_filter=data.get("dont_filter", False),
        meta=_decode_value(data.get("meta") or {}),
        _retry_count=data.get("_retry_count", 0),
        **_decode_value(data.get("session_kwargs") or {}),
    )
    request._callback_name = data.get("callback_name")
    return request


class CheckpointManager:
    """Manages saving and loading checkpoint state to/from disk."""

    CHECKPOINT_FILE = "checkpoint.json"

    def __init__(self, crawldir: str | Path | AsyncPath, interval: float = 300.0):
        self.crawldir = AsyncPath(crawldir)
        self._checkpoint_path = self.crawldir / self.CHECKPOINT_FILE
        self.interval = interval
        if not isinstance(interval, (int, float)):
            raise TypeError("Checkpoints interval must be integer or float.")
        else:
            if interval < 0:
                raise ValueError("Checkpoints interval must be equal or greater than 0.")

    async def has_checkpoint(self) -> bool:
        """Check if a checkpoint exists."""
        return await self._checkpoint_path.exists()

    async def save(self, data: CheckpointData) -> None:
        """Save checkpoint data to disk atomically."""
        await self.crawldir.mkdir(parents=True, exist_ok=True)

        temp_path = self._checkpoint_path.with_suffix(".tmp")

        try:
            payload = {
                "requests": [_request_to_dict(r) for r in data.requests],
                "seen": [_encode_value(fp) for fp in data.seen],
            }
            serialized = orjson.dumps(payload)
            async with await anyio.open_file(temp_path, "wb") as f:
                await f.write(serialized)

            # replace(), not rename(): on Windows rename() raises if the destination
            # already exists, which would break every save after the first one.
            await temp_path.replace(self._checkpoint_path)

            log.info(f"Checkpoint saved: {len(data.requests)} requests, {len(data.seen)} seen URLs")
        except Exception as e:
            # Clean up temp file if it exists
            if await temp_path.exists():
                await temp_path.unlink()
            log.error(f"Failed to save checkpoint: {e}")
            raise

    async def load(self) -> Optional[CheckpointData]:
        """Load checkpoint data from disk.

        Returns None if no checkpoint exists or if loading fails.
        """
        if not await self.has_checkpoint():
            return None

        try:
            async with await anyio.open_file(self._checkpoint_path, "rb") as f:
                content = await f.read()
                payload = orjson.loads(content)
                data = CheckpointData(
                    requests=[_request_from_dict(r) for r in payload["requests"]],
                    seen={_decode_value(fp) for fp in payload["seen"]},
                )

            log.info(
                f"Checkpoint loaded: {len(data.requests)} requests, {len(data.seen)} seen URLs"
            )
            return data

        except Exception as e:
            log.error(f"Failed to load checkpoint (starting fresh): {e}")
            return None

    async def cleanup(self) -> None:
        """Delete checkpoint file after successful completion."""
        try:
            if await self._checkpoint_path.exists():
                await self._checkpoint_path.unlink()
            log.debug("Checkpoint file cleaned up")
        except Exception as e:
            log.warning(f"Failed to cleanup checkpoint file: {e}")
