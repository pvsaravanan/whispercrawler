# Contributing to WhisperCrawler

Thank you for your interest in contributing to WhisperCrawler. We welcome contributions from the community to help make this framework more robust, stealthy, and adaptive.

## Development Setup

To set up your development environment, follow these steps:

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/WhisperCrawl/WhisperCrawler.git
    cd WhisperCrawler
    ```

2.  **Install Dependencies**:
    We recommend using a virtual environment. Install the package with development and all optional dependencies:
    ```bash
    pip install -e ".[dev,fetchers,mcp]"
    ```

3.  **Install Browser Binaries**:
    Required for dynamic and stealth fetchers:
    ```bash
    whispercrawler install --force
    ```

4.  **Install Pre-commit Hooks** (Optional but recommended):
    ```bash
    pre-commit install
    ```

## Development Workflow

### Code Style and Standards
We maintain high standards for code quality. Please ensure your contributions adhere to the following:

*   **Type Annotations**: All functions and methods must have full type hints. We use MyPy in strict mode.
*   **Linting and Formatting**: We use [Ruff](https://github.com/astral-sh/ruff) for both linting and formatting. Line length is set to 100 characters.
*   **Naming Conventions**:
    *   Classes: `PascalCase`
    *   Functions/Variables: `snake_case`
    *   Constants: `UPPER_SNAKE_CASE`

### Testing
All new features and bug fixes must be accompanied by tests. We use `pytest` with `asyncio` support.

*   Run all tests:
    ```bash
    pytest
    ```
*   Run tests with coverage (minimum required: 80%):
    ```bash
    pytest --cov=whispercrawler
    ```

### Quality Checks
Before submitting a pull request, please run the following checks:

```bash
# Linting checks
ruff check .

# Formatting
ruff format .

# Type checking
mypy whispercrawler/
```

## Pull Request Process

1.  **Create a Branch**: Use a descriptive name for your branch (e.g., `feature/adaptive-improvement` or `fix/session-leak`).
2.  **Commit Changes**: Write clear, concise commit messages.
3.  **Update Documentation**: If your change adds new functionality or changes existing APIs, update the appropriate documentation files and docstrings.
4.  **Submit PR**: Ensure all tests and linting checks pass in your local environment before opening a PR.

## Security and Stealth
WhisperCrawler prioritizes stealth and anti-bot bypass. When contributing to fetchers or engines:
*   Ensure that browser fingerprints remain consistent and realistic.
*   Avoid adding code that could be easily detected by common WAFs (e.g., Cloudflare, Akamai).
*   Test stealth features against target sites if possible.

## License
By contributing to WhisperCrawler, you agree that your contributions will be licensed under the project's MIT License.
