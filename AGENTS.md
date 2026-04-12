# AGENTS.md - WhisperCrawl Development Guide

This guide provides essential information for AI coding agents working with the WhisperCrawl repository.

## Project Overview

WhisperCrawl is a Python-based adaptive web scraping framework that provides fast, stealthy, and self-healing web scraping capabilities. It supports multiple fetching strategies (static HTTP, browser automation, stealth mode) and includes adaptive parsing that survives website redesigns.

**Python Version:** 3.10+ (project targets Python 3.10, 3.11, 3.12)  
**Package Manager:** pip with pyproject.toml (Hatchling build backend)  
**Testing Framework:** pytest with asyncio support  
**Linting/Formatting:** Ruff (replaces Black, isort, flake8)  
**Type Checking:** MyPy with strict mode

## Build, Test, and Lint Commands

### Development Setup
```bash
# Install with development dependencies
pip install -e ".[dev,fetchers,mcp]"

# Install browser dependencies (required for some fetchers)
whispercrawler install --force

# Install pre-commit hooks (optional)
pre-commit install
```

### Testing Commands
```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest whispercrawler/tests/core/test_storage_core.py

# Run specific test function
pytest whispercrawler/tests/fetchers/async/test_dynamic.py::test_specific_function

# Run tests with coverage
pytest --cov=whispercrawler --cov-report=html

# Run specific test directory
pytest whispercrawler/tests/fetchers/
pytest whispercrawler/tests/core/
pytest whispercrawler/tests/parser/
```

### Linting and Formatting
```bash
# Run ruff linter
ruff check .

# Run ruff linter with auto-fix
ruff check . --fix

# Run ruff formatter
ruff format .

# Run type checking
mypy whispercrawler/

# Run security scanning
bandit -r whispercrawler/ -c .bandit.yml

# Run pre-commit hooks manually
pre-commit run --all-files
```

### Running the Application
```bash
# CLI scraping
whispercrawler extract get https://example.com

# Interactive shell
whispercrawler shell

# Start MCP server for AI agents
whispercrawler-mcp
```

## Code Style Guidelines

### Import Organization
```python
# 1. Standard library imports (grouped logically)
from pathlib import Path
from typing import Optional, Union

# 2. Third-party library imports (alphabetical)
from lxml.html import HtmlElement
from rich.console import Console

# 3. Local imports (grouped by module)
from whispercrawler.core._types import Any, Dict, List
from whispercrawler.core.custom_types import AttributesHandler
```

**Rules:**
- Standard library first, then third-party, then local imports
- Use multi-line imports with parentheses for readability
- Alias imports when needed for clarity
- Group type imports from `_types.py`

### Naming Conventions
- **Classes:** PascalCase (`Selector`, `DynamicFetcher`, `AttributesHandler`)
- **Functions/Methods:** snake_case (`find_all`, `css_first`, `_merge_request_args`)
- **Variables:** snake_case (`_whitelisted`, `__DEFAULT_DB_FILE__`)
- **Constants:** UPPER_SNAKE_CASE (`SUPPORTED_HTTP_METHODS`)
- **Private/Protected:** Single underscore prefix (`_storage`, `_validate_input`)
- **Private Class Members:** Double underscore prefix (`__adaptive_enabled`)

### Type Annotations

**Always use type hints for all function parameters and return values:**
```python
def css(
    self, 
    selector: str, 
    identifier: str = "", 
    adaptive: bool = False,
    auto_save: bool = False, 
    percentage: int = 0,
) -> "Selectors":
```

**Modern Python 3.10+ union syntax:**
```python
content: str | bytes  # Preferred over Union[str, bytes]
result: List[HtmlElement | str]
```

**Use TypeVar for generics:**
```python
_T = TypeVar("_T")
_TextHandlerType = TypeVar("_TextHandlerType", bound="TextHandler")
```

**Function overloads for different return types:**
```python
@overload
def find_by_text(self, text: str, first_match: Literal[True]) -> "Selector": ...

@overload  
def find_by_text(self, text: str, first_match: Literal[False]) -> "Selectors": ...
```

### Error Handling

**Use descriptive error messages:**
```python
if root is None and content is None:
    raise ValueError("Selector class needs HTML content, or root arguments to work")
```

**Chain exceptions properly:**
```python
try:
    xpath_selector = _css_to_xpath(selector)
    return self.xpath(xpath_selector, identifier, adaptive, auto_save, percentage)
except (SelectorError, SelectorSyntaxError) as e:
    raise SelectorSyntaxError(f"Invalid CSS selector '{selector}': {str(e)}") from e
```

**Handle optional dependencies gracefully:**
```python
try:
    from playwright import async_api
except ImportError as e:
    raise ModuleNotFoundError("Install playwright: pip install 'whispercrawler[fetchers]'") from e
```

### Documentation and Docstrings

**Use comprehensive parameter documentation:**
```python
def css(self, selector: str, adaptive: bool = False) -> "Selectors":
    """Search the current tree with CSS3 selectors

    **Important: Use the identifier argument if you plan to use adaptive mode later**

    :param selector: The CSS3 selector to be used
    :param adaptive: Enable element relocation if element was 'saved' before  
    :param identifier: String used to save/retrieve element data in adaptive mode
    :param auto_save: Automatically save new elements for adaptive use later
    :param percentage: Minimum percentage to accept while adaptive is working
    :return: `Selectors` class containing matched elements
    """
```

### Class Structure

**Use `__slots__` for performance when appropriate:**
```python
class TextHandler(str):
    __slots__ = ()

class Selector:
    __slots__ = ("url", "encoding", "_root", "_storage", "huge_tree", ...)
```

**Organize class methods logically:**
```python
class MyClass:
    def __init__(self, ...):  # Initialization
    
    def __getitem__(self, ...):  # Magic methods
    def __contains__(self, ...):
    
    @property  # Properties
    def tag(self):
    
    def public_method(self, ...):  # Public methods
    
    def _protected_method(self, ...):  # Protected methods
    def __private_method(self, ...):  # Private methods
```

### Async/Await Patterns

**Provide both sync and async interfaces:**
```python
class SyncFetcher:
    def fetch(self, url: str) -> Response:
        # sync implementation
        
class AsyncFetcher:
    async def fetch(self, url: str) -> Response:
        # async implementation
```

**Use async context managers:**
```python
async with AsyncDynamicSession(**kwargs) as session:
    return await session.fetch(url)
```

## Configuration Files

- **pyproject.toml:** Main project configuration (dependencies, scripts, tool configs)
- **setup.cfg:** Legacy setup configuration  
- **.pre-commit-config.yaml:** Pre-commit hooks (bandit, ruff, vermin)
- **pytest.ini in pyproject.toml:** Test configuration with asyncio_mode = "auto"

## Key Directories

- **whispercrawler/core/:** Core functionality (pagination, schema, analyzer, regex)
- **whispercrawler/engines/:** Scraping engines (static, browser configs)  
- **whispercrawler/fetchers/:** Different fetching strategies (requests, chrome, stealth)
- **whispercrawler/integrations/:** Third-party integrations (Scrapy)
- **whispercrawler/spiders/:** Spider framework (engine, scheduler, session)
- **whispercrawler/tests/:** Comprehensive test suite organized by module
- **docs/:** MkDocs documentation with multi-language support

## Quality Standards

- **Test Coverage:** Minimum 80% (configured in pyproject.toml)
- **Type Checking:** Strict MyPy mode enabled
- **Security:** Bandit security scanning in pre-commit hooks
- **Compatibility:** Vermin checks for Python 3.10+ compatibility
- **Line Length:** 100 characters (Ruff configuration)

## Common Patterns

**Validation patterns:**
```python
if not isinstance(selector_config, dict):
    raise TypeError("Argument `selector_config` must be a dictionary.")
```

**Factory patterns for browser selection:**
```python
def _select_random_browser(impersonate: ImpersonateType) -> Optional[BrowserTypeLiteral]:
    if isinstance(impersonate, list):
        return choice(impersonate) if impersonate else None
    return impersonate
```

**Efficient element searching with pre-compiled selectors:**
```python
_find_all_elements = XPath(".//*")
_find_all_elements_with_spaces = XPath(".//*[normalize-space(text())]")
```

## Advanced API Capabilities

### 1. Automatic Pagination Detection
Use the `next_page` and `all_pages` properties on `Selector` objects to discover navigation links.
```python
next_url = page.next_page
all_links = page.all_pages
```

### 2. Structured Data Extraction
Access parsed JSON-LD and Microdata via the `schemas` property.
```python
product_schemas = page.find_schema("Product")
all_site_data = page.schemas
```

### 3. Page Metadata Analysis
Extract SEO, OpenGraph, and Twitter metadata using the `analyze()` method.
```python
metadata_dict = page.metadata
readable_summary = page.analyze(summary=True)
```

### 4. Programmatic Regex Synthesis
Generate regex patterns from a selection of elements using `generate_regex()`.
```python
# Create a pattern from all links in a list
regex_pattern = page.css("a.product-link").generate_regex(attribute="href")
```

### 5. Scrapy Integration
Use the `@whisper_response` decorator in Scrapy spiders to replace standard selectors with WhisperCrawler's adaptive engine.
```python
from whispercrawler.integrations.scrapy import whisper_response

@whisper_response
def parse(self, response):
    title = response.css("h1::text").get()
```

### 6. Automatic Captcha Solving
Provision an API key from 2Captcha or Anti-Captcha to solving Google ReCaptcha V2 challenges.
```python
from whispercrawler import StealthyFetcher
page = StealthyFetcher.fetch(
    url, 
    captcha_api_key="...",
    captcha_service="2captcha"
)
```

## Development Workflow

1. Make changes following the style guidelines above
2. Run tests: `pytest whispercrawler/tests/` 
3. Run linting: `ruff check . --fix && ruff format .`
4. Run type checking: `mypy whispercrawler/`
5. Ensure coverage: `pytest --cov=whispercrawler`
6. Update documentation if adding new features

Remember: This project emphasizes stealth, performance, and adaptability. When making changes, consider the impact on these core principles.
