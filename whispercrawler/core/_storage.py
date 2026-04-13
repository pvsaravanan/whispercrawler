# MIT License
#
# Copyright (c) 2026, Saravanan P V
#
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the conditions of the BSD-3-Clause License are met.

"""WhisperStorage — adaptive SQLite element fingerprint store."""

from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import TYPE_CHECKING, Any

import orjson

if TYPE_CHECKING:
    from whispercrawler.core._custom_types import PageList
    from whispercrawler.parser import Page

logger = logging.getLogger("whispercrawler.storage")

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS element_fingerprints (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    domain      TEXT NOT NULL,
    selector    TEXT NOT NULL,
    tag         TEXT,
    text_content TEXT,
    attributes  TEXT,
    dom_path    TEXT,
    parent_tag  TEXT,
    parent_attrs TEXT,
    sibling_index   INTEGER,
    sibling_count   INTEGER,
    created_at  TEXT,
    updated_at  TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_domain_selector
    ON element_fingerprints(domain, selector);
"""


class WhisperStorage:
    """Stores and retrieves element fingerprints for adaptive parsing.

    When a CSS or XPath selector stops matching after a site redesign,
    WhisperStorage finds the element by similarity to its stored properties.
    """

    def __init__(self, db_path: str | None = None, domain: str = "") -> None:
        """Initialize storage.

        Args:
            db_path: Path to SQLite database. Defaults to ~/.whispercrawler/adaptive.db
            domain: Domain scope for fingerprints.
        """
        self.domain = domain
        if db_path is None:
            home = Path.home() / ".whispercrawler"
            home.mkdir(parents=True, exist_ok=True)
            self.db_path = str(home / "adaptive.db")
        else:
            db_dir = os.path.dirname(db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
            self.db_path = db_path

        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA_SQL)
        self._conn.commit()

    def _get_dom_path(self, element: Page) -> str:
        """Generate a CSS-like path from root to element."""
        parts: list[str] = []
        current: Any = element
        while current is not None:
            tag = current.tag if hasattr(current, "tag") else ""
            if tag and tag not in ("", "[document]"):
                attrib = current.attrib if hasattr(current, "attrib") else {}
                id_val = attrib.get("id") if attrib else None
                if id_val:
                    parts.append(f"{tag}#{id_val}")
                else:
                    parts.append(tag)
            if hasattr(current, "parent"):
                current = current.parent
            else:
                break
        parts.reverse()
        return " > ".join(parts)

    def save(self, selector: str, element: Page) -> None:
        """Store a fingerprint of element matched by selector.

        If record exists for (domain, selector), update it.
        Extracts: tag, text_content (first 500 chars), attributes dict,
        dom_path, parent tag+attrs, sibling_index, sibling_count.
        """
        now = datetime.now(timezone.utc).isoformat()
        tag = element.tag if hasattr(element, "tag") else ""
        text_content = ""
        if hasattr(element, "text") and element.text:
            text_content = str(element.text)[:500]

        attrib_dict: dict[str, str] = {}
        if hasattr(element, "attrib") and element.attrib:
            attrib_dict = dict(element.attrib)

        dom_path = self._get_dom_path(element)

        parent_tag = ""
        parent_attrs_dict: dict[str, str] = {}
        if hasattr(element, "parent") and element.parent is not None:
            parent = element.parent
            parent_tag = parent.tag if hasattr(parent, "tag") else ""
            if hasattr(parent, "attrib") and parent.attrib:
                parent_attrs_dict = dict(parent.attrib)

        sibling_index = 0
        sibling_count = 0
        if hasattr(element, "parent") and element.parent is not None:
            parent = element.parent
            if hasattr(parent, "children"):
                siblings = list(parent.children)
                sibling_count = len(siblings)
                for i, sib in enumerate(siblings):
                    if sib is element or (
                        hasattr(sib, "_element")
                        and hasattr(element, "_element")
                        and sib._element is element._element
                    ):
                        sibling_index = i
                        break

        attrs_json = orjson.dumps(attrib_dict).decode("utf-8")
        parent_attrs_json = orjson.dumps(parent_attrs_dict).decode("utf-8")

        self._conn.execute(
            """
            INSERT INTO element_fingerprints
                (domain, selector, tag, text_content, attributes, dom_path,
                 parent_tag, parent_attrs, sibling_index, sibling_count,
                 created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(domain, selector) DO UPDATE SET
                tag=excluded.tag, text_content=excluded.text_content,
                attributes=excluded.attributes, dom_path=excluded.dom_path,
                parent_tag=excluded.parent_tag, parent_attrs=excluded.parent_attrs,
                sibling_index=excluded.sibling_index, sibling_count=excluded.sibling_count,
                updated_at=excluded.updated_at
            """,
            (
                self.domain,
                selector,
                tag,
                text_content,
                attrs_json,
                dom_path,
                parent_tag,
                parent_attrs_json,
                sibling_index,
                sibling_count,
                now,
                now,
            ),
        )
        self._conn.commit()
        logger.debug("Saved fingerprint for selector=%s domain=%s", selector, self.domain)

    def retrieve(self, selector: str) -> dict[str, Any] | None:
        """Return stored fingerprint dict for (domain, selector), or None."""
        cursor = self._conn.execute(
            "SELECT * FROM element_fingerprints WHERE domain = ? AND selector = ?",
            (self.domain, selector),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        result = dict(row)
        if result.get("attributes"):
            result["attributes"] = orjson.loads(result["attributes"])
        if result.get("parent_attrs"):
            result["parent_attrs"] = orjson.loads(result["parent_attrs"])
        return result

    def compute_similarity(self, fingerprint: dict[str, Any], candidate: Page) -> float:
        """Score similarity between stored fingerprint and a candidate Page element.

        Returns float 0.0–1.0.

        Scoring weights:
            tag match          30% — 1.0 if tags match, 0.0 otherwise
            text similarity    25% — SequenceMatcher ratio on text_content
            attribute overlap  25% — Jaccard similarity on attribute key sets
            dom_path similarity 20% — SequenceMatcher ratio on dom_path strings
        """
        score = 0.0

        # Tag match (30%)
        candidate_tag = candidate.tag if hasattr(candidate, "tag") else ""
        fp_tag = fingerprint.get("tag", "")
        if fp_tag and candidate_tag and fp_tag == candidate_tag:
            score += 0.30

        # Text similarity (25%)
        fp_text = fingerprint.get("text_content", "") or ""
        candidate_text = ""
        if hasattr(candidate, "text") and candidate.text:
            candidate_text = str(candidate.text)[:500]
        if fp_text or candidate_text:
            text_ratio = SequenceMatcher(None, fp_text, candidate_text).ratio()
            score += 0.25 * text_ratio

        # Attribute overlap (25%) — Jaccard similarity
        fp_attrs = fingerprint.get("attributes", {}) or {}
        if isinstance(fp_attrs, str):
            fp_attrs = orjson.loads(fp_attrs)
        candidate_attrs: dict[str, str] = {}
        if hasattr(candidate, "attrib") and candidate.attrib:
            candidate_attrs = dict(candidate.attrib)
        fp_keys = set(fp_attrs.keys())
        cand_keys = set(candidate_attrs.keys())
        if fp_keys or cand_keys:
            jaccard = len(fp_keys & cand_keys) / len(fp_keys | cand_keys)
            score += 0.25 * jaccard

        # DOM path similarity (20%)
        fp_path = fingerprint.get("dom_path", "") or ""
        candidate_path = self._get_dom_path(candidate)
        if fp_path or candidate_path:
            path_ratio = SequenceMatcher(None, fp_path, candidate_path).ratio()
            score += 0.20 * path_ratio

        return score

    def find_best_match(
        self,
        selector: str,
        candidates: PageList,
        threshold: float = 0.6,
    ) -> Page | None:
        """Retrieve fingerprint for selector, score all candidates.

        Returns highest-scoring Page above threshold, or None.
        """
        fingerprint = self.retrieve(selector)
        if fingerprint is None:
            return None

        best_score = 0.0
        best_candidate: Page | None = None

        for candidate in candidates:
            similarity = self.compute_similarity(fingerprint, candidate)
            if similarity > best_score:
                best_score = similarity
                best_candidate = candidate

        if best_score >= threshold:
            logger.info(
                "Adaptive match found for selector=%s score=%.3f",
                selector,
                best_score,
            )
            return best_candidate
        return None

    def clear(self, domain: str | None = None) -> int:
        """Delete all records for domain (or all records if domain is None).

        Returns count of deleted rows.
        """
        if domain is not None:
            cursor = self._conn.execute(
                "DELETE FROM element_fingerprints WHERE domain = ?", (domain,)
            )
        else:
            cursor = self._conn.execute("DELETE FROM element_fingerprints")
        self._conn.commit()
        count = cursor.rowcount
        logger.info("Cleared %d fingerprint records (domain=%s)", count, domain)
        return count

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def __del__(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass
