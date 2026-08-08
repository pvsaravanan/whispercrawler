# Command Line Interface

Since v0.3, whispercrawler includes a powerful command-line interface that provides three main capabilities:

1. **Interactive Shell**: An interactive Web Scraping shell based on IPython that provides many shortcuts and useful tools
2. **Extract Commands**: Scrape websites from the terminal without any programming
3. **Utility Commands**: Installation and management tools

```bash
# Launch interactive shell
whispercrawler shell

# Convert the content of a page to markdown and save it to a file
whispercrawler extract get "https://example.com" content.md

# Get help for any command
whispercrawler --help
whispercrawler extract --help
```

## Requirements
The interactive shell and `extract --help`/`install`/etc. commands work out of the box with the base install — `click`, `rich`, and `ipython` are core dependencies, not an extra.

Actually fetching pages (`whispercrawler extract get/post/...`, `whispercrawler shell` making requests) needs the `fetchers` extra and its browser binaries:
```bash
pip install "whispercrawler[fetchers]"

whispercrawler install
```
This downloads all browsers, along with their system dependencies and fingerprint manipulation dependencies. See [Installation](../installation.md) for the full breakdown.
