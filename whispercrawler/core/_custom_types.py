# MIT License
#
# Copyright (c) 2026, Saravanan P V
#
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the conditions of the BSD-3-Clause License are met.

"""Custom types: TextWhisper, AttributeMap, PageList."""

from __future__ import annotations

import re
import unicodedata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class TextWhisper(str):
    """A str subclass returned by all text-extraction methods.

    Provides chainable transformations, regex helpers, and type coercion.
    """

    def clean(self) -> TextWhisper:
        """Strip leading/trailing whitespace and collapse internal whitespace to single spaces."""
        return TextWhisper(re.sub(r"\s+", " ", self.strip()))

    def normalize(self) -> TextWhisper:
        """Apply unicode NFKC normalization."""
        return TextWhisper(unicodedata.normalize("NFKC", self))

    def to_int(self, default: int = 0) -> int:
        """Parse self to int. Return default on failure."""
        try:
            # Strip non-numeric chars except minus sign and digits
            cleaned = re.sub(r"[^\d\-]", "", self.strip())
            return int(cleaned) if cleaned else default
        except (ValueError, TypeError):
            return default

    def to_float(self, default: float = 0.0) -> float:
        """Parse self to float. Return default on failure."""
        try:
            cleaned = re.sub(r"[^\d\.\-]", "", self.strip())
            return float(cleaned) if cleaned else default
        except (ValueError, TypeError):
            return default

    def re(self, pattern: str, group: int = 1, default: str | None = None) -> TextWhisper | None:
        """Apply regex pattern, return group match as TextWhisper or default."""
        match = re.search(pattern, self)
        if match:
            try:
                result = match.group(group)
                return TextWhisper(result) if result is not None else None
            except IndexError:
                return TextWhisper(default) if default is not None else None
        return TextWhisper(default) if default is not None else None

    def re_all(self, pattern: str) -> list[TextWhisper]:
        """Return all regex matches as list of TextWhisper."""
        return [TextWhisper(m) for m in re.findall(pattern, self)]

    def to_markdown(self) -> TextWhisper:
        """Convert HTML content in self to Markdown using markdownify."""
        from markdownify import markdownify

        return TextWhisper(markdownify(str(self)).strip())

    def contains(self, substr: str, case_sensitive: bool = True) -> bool:
        """Return True if self contains substr."""
        if case_sensitive:
            return substr in self
        return substr.lower() in self.lower()

    @property
    def length(self) -> int:
        """Alias for len(self)."""
        return len(self)

    def __repr__(self) -> str:
        preview = self[:50]
        suffix = "..." if len(self) > 50 else ""
        return f"<TextWhisper '{preview}{suffix}'>"


class AttributeMap(dict):  # type: ignore[type-arg]
    """A dict subclass representing an element's HTML attributes.

    Provides convenience accessors and always returns TextWhisper values.
    """

    def get_list(self, key: str, separator: str = ",") -> list[TextWhisper]:
        """Split attribute value by separator and return as list of TextWhisper."""
        value = self.get(key)
        if value is None:
            return []
        return [TextWhisper(v.strip()) for v in str(value).split(separator) if v.strip()]

    def has(self, key: str) -> bool:
        """Return True if key exists in attributes."""
        return key in self

    def __getattr__(self, name: str) -> TextWhisper | None:
        """Proxy attribute access to dict key lookup. Return TextWhisper or None."""
        if name.startswith("_"):
            raise AttributeError(name)
        value = self.get(name)
        return TextWhisper(str(value)) if value is not None else None

    def __missing__(self, key: str) -> None:
        """Return None for missing keys instead of raising KeyError."""
        return None

    def get(self, key: str, default: str | None = None) -> TextWhisper | None:  # type: ignore[override]
        """Get attribute value as TextWhisper."""
        value = super().get(key, default)
        return TextWhisper(str(value)) if value is not None else None


class PageList(list):  # type: ignore[type-arg]
    """A list subclass of Page objects.

    Supports chained CSS/XPath selection and bulk text/attribute extraction.
    """

    def css(self, selector: str, **kwargs: object) -> PageList:
        """Run CSS selector on each Page, return flat PageList of all matches."""
        result = PageList()
        for page in self:
            if hasattr(page, "css"):
                result.extend(page.css(selector, **kwargs))
        return result

    def xpath(self, selector: str, **kwargs: object) -> PageList:
        """Run XPath on each Page, return flat PageList of all matches."""
        result = PageList()
        for page in self:
            if hasattr(page, "xpath"):
                result.extend(page.xpath(selector, **kwargs))
        return result

    def get(self, default: str | None = None) -> TextWhisper | None:
        """Return text of first element, or default if list is empty."""
        if not self:
            return TextWhisper(default) if default is not None else None
        first = self[0]
        if isinstance(first, TextWhisper):
            return first
        if hasattr(first, "text"):
            return first.text
        return TextWhisper(str(first))

    def getall(self) -> list[TextWhisper]:
        """Return list of text values from all elements."""
        results: list[TextWhisper] = []
        for item in self:
            if isinstance(item, TextWhisper):
                results.append(item)
            elif hasattr(item, "text"):
                results.append(item.text)
            else:
                results.append(TextWhisper(str(item)))
        return results

    def re(self, pattern: str) -> list[TextWhisper]:
        """Apply regex pattern across all element texts. Return all matches."""
        results: list[TextWhisper] = []
        for item in self:
            text_val = (
                item
                if isinstance(item, str)
                else (item.text if hasattr(item, "text") else str(item))
            )
            results.extend(TextWhisper(m) for m in re.findall(pattern, str(text_val)))
        return results

    def re_first(self, pattern: str, default: str | None = None) -> TextWhisper | None:
        """Return first regex match across all elements, or default."""
        matches = self.re(pattern)
        if matches:
            return matches[0]
        return TextWhisper(default) if default is not None else None

    def attribs(self, key: str) -> list[TextWhisper]:
        """Return list of attribute values for key across all elements."""
        results: list[TextWhisper] = []
        for item in self:
            if hasattr(item, "attrib"):
                attr_val = item.attrib.get(key)
                if attr_val is not None:
                    results.append(TextWhisper(str(attr_val)))
        return results

    @property
    def length(self) -> int:
        """Alias for len(self)."""
        return len(self)
