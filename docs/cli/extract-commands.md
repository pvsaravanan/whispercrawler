# WhisperCrawler Extract Command Guide

**Web Scraping through the terminal without requiring any programming!**

The `whispercrawler extract` command lets you download and extract content from websites directly from your terminal without writing any code. Ideal for beginners, researchers, and anyone requiring rapid web data extraction.

!!! success "Prerequisites"

    1. You've completed or read the [Fetchers basics](../fetching/choosing.md) page to understand what the [Response object](../fetching/choosing.md#response-object) is and which fetcher to use.
    2. You've completed or read the [Querying elements](../parsing/selection.md) page to understand how to find/extract elements from the [Selector](../parsing/main_classes.md#selector)/[Response](../fetching/choosing.md#response-object) object.
    3. You've completed or read the [Main classes](../parsing/main_classes.md) page to know what properties/methods the [Response](../fetching/choosing.md#response-object) class is inheriting from the [Selector](../parsing/main_classes.md#selector) class.
    4. You've completed or read at least one page from the fetchers section to use here for requests: [HTTP requests](../fetching/static.md), [Dynamic websites](../fetching/dynamic.md), or [Dynamic websites with hard protections](../fetching/stealthy.md).


## What is the Extract Command group?

The extract command is a set of simple terminal tools that:

- **Downloads web pages** and saves their content to files.
- **Converts HTML to readable formats** like Markdown, keeps it as HTML, or just extracts the text content of the page.
- **Supports custom CSS selectors** to extract specific parts of the page.
- **Handles HTTP requests and fetching through browsers**
- **Highly customizable** with custom headers, cookies, proxies, and the rest of the options. Almost all the options available through the code are also accessible through the command line.

## Quick Start

- **Basic Website Download**

    Download a website's text content as clean, readable text:
    ```bash
    whispercrawler extract get "https://example.com" page_content.txt
    ```
    This makes an HTTP GET request and saves the webpage's text content to `page_content.txt`.

- **Save as Different Formats**

    Choose your output format by changing the file extension:
    ```bash
    # Convert the HTML content to Markdown, then save it to the file (great for documentation)
    whispercrawler extract get "https://blog.example.com" article.md
    
    # Save the HTML content as it is to the file
    whispercrawler extract get "https://example.com" page.html
    
    # Save a clean version of the text content of the webpage to the file
    whispercrawler extract get "https://example.com" content.txt
  
    # Or use the Docker image with something like this:
    docker run -v $(pwd)/output:/output whispercrawler extract get "https://blog.example.com" /output/article.md 
    ```

- **Extract Specific Content**

    All commands can use CSS selectors to extract specific parts of the page through `--css-selector` or `-s` as you will see in the examples below.

## Available Commands

You can display the available commands through `whispercrawler extract --help` to get the following list:
```bash
Usage: whispercrawler extract [OPTIONS] COMMAND [ARGS]...

  Fetch web pages using various fetchers and extract full/selected HTML content as HTML, Markdown, or extract text content.

Options:
  --help  Show this message and exit.

Commands:
  get             Perform a GET request and save the content to a file.
  post            Perform a POST request and save the content to a file.
  put             Perform a PUT request and save the content to a file.
  delete          Perform a DELETE request and save the content to a file.
  fetch           Use DynamicFetcher to fetch content with browser...
  stealthy-fetch  Use StealthyFetcher to fetch content with advanced...
```

We will go through each command in detail below.

### HTTP Requests

1. **GET Request**

    The most common command for downloading website content:
    
    ```bash
    whispercrawler extract get [URL] [OUTPUT_FILE] [OPTIONS]
    ```
    
    **Examples:**
    ```bash
    # Basic download
    whispercrawler extract get "https://news.site.com" news.md
    
    # Download with custom timeout
    whispercrawler extract get "https://example.com" content.txt --timeout 60
    
    # Extract only specific content using CSS selectors
    whispercrawler extract get "https://blog.example.com" articles.md --css-selector "article"
   
    # Send a request with cookies
    whispercrawler extract get "https://whispercrawler.requestcatcher.com" content.md --cookies "session=abc123; user=john"
   
    # Add user agent
    whispercrawler extract get "https://api.site.com" data.json -H "User-Agent: MyBot 1.0"
    
    # Add multiple headers
    whispercrawler extract get "https://site.com" page.html -H "Accept: text/html" -H "Accept-Language: en-US"
    ```
    Get the available options for the command with `whispercrawler extract get --help` as follows:
    ```bash
    Usage: whispercrawler extract get [OPTIONS] URL OUTPUT_FILE
    
      Perform a GET request and save the content to a file.
    
      The output file path can be an HTML file, a Markdown file of the HTML content, or the text content itself. Use file extensions (`.html`/`.md`/`.txt`) respectively.
    
    Options:
      -H, --headers TEXT                             HTTP headers in format "Key: Value" (can be used multiple times)
      --cookies TEXT                                 Cookies string in format "name1=value1;name2=value2"
      --timeout INTEGER                              Request timeout in seconds (default: 30)
      --proxy TEXT                                   Proxy URL in format "http://username:password@host:port"
      -s, --css-selector TEXT                        CSS selector to extract specific content from the page. It returns all matches.
      -p, --params TEXT                              Query parameters in format "key=value" (can be used multiple times)
      --follow-redirects / --no-follow-redirects     Whether to follow redirects (default: True)
      --verify / --no-verify                         Whether to verify SSL certificates (default: True)
      --impersonate TEXT                             Browser to impersonate (e.g., chrome, firefox).
      --stealthy-headers / --no-stealthy-headers     Use stealthy browser headers (default: True)
      --help                                         Show this message and exit.
    
    ```
    Note that the options will work in the same way for all other request commands, so no need to repeat them.

2. **Post Request**
    
    ```bash
    whispercrawler extract post [URL] [OUTPUT_FILE] [OPTIONS]
    ```
    
    **Examples:**
    ```bash
    # Submit form data
    whispercrawler extract post "https://api.site.com/search" results.html --data "query=python&type=tutorial"
    
    # Send JSON data
    whispercrawler extract post "https://api.site.com" response.json --json '{"username": "test", "action": "search"}'
    ```
    Get the available options for the command with `whispercrawler extract post --help` as follows:
    ```bash
    Usage: whispercrawler extract post [OPTIONS] URL OUTPUT_FILE
    
      Perform a POST request and save the content to a file.
    
      The output file path can be an HTML file, a Markdown file of the HTML content, or the text content itself. Use file extensions (`.html`/`.md`/`.txt`) respectively.
    
    Options:
      -d, --data TEXT                                Form data to include in the request body (as string, ex: "param1=value1&param2=value2")
      -j, --json TEXT                                JSON data to include in the request body (as string)
      -H, --headers TEXT                             HTTP headers in format "Key: Value" (can be used multiple times)
      --cookies TEXT                                 Cookies string in format "name1=value1;name2=value2"
      --timeout INTEGER                              Request timeout in seconds (default: 30)
      --proxy TEXT                                   Proxy URL in format "http://username:password@host:port"
      -s, --css-selector TEXT                        CSS selector to extract specific content from the page. It returns all matches.
      -p, --params TEXT                              Query parameters in format "key=value" (can be used multiple times)
      --follow-redirects / --no-follow-redirects     Whether to follow redirects (default: True)
      --verify / --no-verify                         Whether to verify SSL certificates (default: True)
      --impersonate TEXT                             Browser to impersonate (e.g., chrome, firefox).
      --stealthy-headers / --no-stealthy-headers     Use stealthy browser headers (default: True)
      --help                                         Show this message and exit.
    
    ```

3. **Put Request**
    
    ```bash
    whispercrawler extract put [URL] [OUTPUT_FILE] [OPTIONS]
    ```
    
    **Examples:**
    ```bash
    # Send data
    whispercrawler extract put "https://whispercrawler.requestcatcher.com/put" results.html --data "update=info" --impersonate "firefox"
    
    # Send JSON data
    whispercrawler extract put "https://whispercrawler.requestcatcher.com/put" response.json --json '{"username": "test", "action": "search"}'
    ```
    Get the available options for the command with `whispercrawler extract put --help` as follows:
    ```bash
    Usage: whispercrawler extract put [OPTIONS] URL OUTPUT_FILE
    
      Perform a PUT request and save the content to a file.
    
      The output file path can be an HTML file, a Markdown file of the HTML content, or the text content itself. Use file extensions (`.html`/`.md`/`.txt`) respectively.
    
    Options:
      -d, --data TEXT                                Form data to include in the request body
      -j, --json TEXT                                JSON data to include in the request body (as string)
      -H, --headers TEXT                             HTTP headers in format "Key: Value" (can be used multiple times)
      --cookies TEXT                                 Cookies string in format "name1=value1;name2=value2"
      --timeout INTEGER                              Request timeout in seconds (default: 30)
      --proxy TEXT                                   Proxy URL in format "http://username:password@host:port"
      -s, --css-selector TEXT                        CSS selector to extract specific content from the page. It returns all matches.
      -p, --params TEXT                              Query parameters in format "key=value" (can be used multiple times)
      --follow-redirects / --no-follow-redirects     Whether to follow redirects (default: True)
      --verify / --no-verify                         Whether to verify SSL certificates (default: True)
      --impersonate TEXT                             Browser to impersonate (e.g., chrome, firefox).
      --stealthy-headers / --no-stealthy-headers     Use stealthy browser headers (default: True)
      --help                                         Show this message and exit.
    ```

4. **Delete Request**
    
    ```bash
    whispercrawler extract delete [URL] [OUTPUT_FILE] [OPTIONS]
    ```
    
    **Examples:**
    ```bash
    # Send data
    whispercrawler extract delete "https://whispercrawler.requestcatcher.com/delete" results.html
    
    # Send JSON data
    whispercrawler extract delete "https://whispercrawler.requestcatcher.com/" response.txt --impersonate "chrome"
    ```
    Get the available options for the command with `whispercrawler extract delete --help` as follows:
    ```bash
    Usage: whispercrawler extract delete [OPTIONS] URL OUTPUT_FILE
    
      Perform a DELETE request and save the content to a file.
    
      The output file path can be an HTML file, a Markdown file of the HTML content, or the text content itself. Use file extensions (`.html`/`.md`/`.txt`) respectively.
    
    Options:
      -H, --headers TEXT                             HTTP headers in format "Key: Value" (can be used multiple times)
      --cookies TEXT                                 Cookies string in format "name1=value1;name2=value2"
      --timeout INTEGER                              Request timeout in seconds (default: 30)
      --proxy TEXT                                   Proxy URL in format "http://username:password@host:port"
      -s, --css-selector TEXT                        CSS selector to extract specific content from the page. It returns all matches.
      -p, --params TEXT                              Query parameters in format "key=value" (can be used multiple times)
      --follow-redirects / --no-follow-redirects     Whether to follow redirects (default: True)
      --verify / --no-verify                         Whether to verify SSL certificates (default: True)
      --impersonate TEXT                             Browser to impersonate (e.g., chrome, firefox).
      --stealthy-headers / --no-stealthy-headers     Use stealthy browser headers (default: True)
      --help                                         Show this message and exit.
    ```

### Browsers fetching

1. **fetch - Handle Dynamic Content**

    For websites that load content with dynamic content or have slight protection
    
    ```bash
    whispercrawler extract fetch [URL] [OUTPUT_FILE] [OPTIONS]
    ```
    
    **Examples:**
    ```bash
    # Wait for JavaScript to load content and finish network activity
    whispercrawler extract fetch "https://whispercrawler.requestcatcher.com/" content.md --network-idle
    
    # Wait for specific content to appear
    whispercrawler extract fetch "https://whispercrawler.requestcatcher.com/" data.txt --wait-selector ".content-loaded"
    
    # Run in visible browser mode (helpful for debugging)
    whispercrawler extract fetch "https://whispercrawler.requestcatcher.com/" page.html --no-headless --disable-resources
    ```
    Get the available options for the command with `whispercrawler extract fetch --help` as follows:
    ```bash
    Usage: whispercrawler extract fetch [OPTIONS] URL OUTPUT_FILE
    
      Use DynamicFetcher to fetch content with browser automation.
    
      The output file path can be an HTML file, a Markdown file of the HTML content, or the text content itself. Use file extensions (`.html`/`.md`/`.txt`) respectively.
    
    Options:
      --headless / --no-headless                  Run browser in headless mode (default: True)
      --disable-resources / --enable-resources    Drop unnecessary resources for speed boost (default: False)
      --network-idle / --no-network-idle          Wait for network idle (default: False)
      --timeout INTEGER                           Timeout in milliseconds (default: 30000)
      --wait INTEGER                              Additional wait time in milliseconds after page load (default: 0)
      -s, --css-selector TEXT                     CSS selector to extract specific content from the page. It returns all matches.
      --wait-selector TEXT                        CSS selector to wait for before proceeding
      --locale TEXT                               Specify user locale. Defaults to the system default locale.
      --real-chrome/--no-real-chrome              If you have a Chrome browser installed on your device, enable this, and the Fetcher will launch an instance of your browser and use it. (default: False)
      --proxy TEXT                                Proxy URL in format "http://username:password@host:port"
      -H, --extra-headers TEXT                    Extra headers in format "Key: Value" (can be used multiple times)
      --help                                      Show this message and exit.
    ```

2. **stealthy-fetch - Bypass Protection**

    For websites with anti-bot protection or Cloudflare protection
    
    ```bash
    whispercrawler extract stealthy-fetch [URL] [OUTPUT_FILE] [OPTIONS]
    ```
    
    **Examples:**
    ```bash
    # Bypass basic protection
    whispercrawler extract stealthy-fetch "https://whispercrawler.requestcatcher.com" content.md
    
    # Solve Cloudflare challenges
    whispercrawler extract stealthy-fetch "https://nopecha.com/demo/cloudflare" data.txt --solve-cloudflare --css-selector "#padded_content a"
    
    # Use a proxy for anonymity.
    whispercrawler extract stealthy-fetch "https://site.com" content.md --proxy "http://proxy-server:8080"
    ```
    Get the available options for the command with `whispercrawler extract stealthy-fetch --help` as follows:
    ```bash
    Usage: whispercrawler extract stealthy-fetch [OPTIONS] URL OUTPUT_FILE
    
      Use StealthyFetcher to fetch content with advanced stealth features.
    
      The output file path can be an HTML file, a Markdown file of the HTML content, or the text content itself. Use file extensions (`.html`/`.md`/`.txt`) respectively.
    
    Options:
      --headless / --no-headless                  Run browser in headless mode (default: True)
      --disable-resources / --enable-resources    Drop unnecessary resources for speed boost (default: False)
      --block-webrtc / --allow-webrtc             Block WebRTC entirely (default: False)
      --solve-cloudflare / --no-solve-cloudflare  Solve Cloudflare challenges (default: False)
      --allow-webgl / --block-webgl               Allow WebGL (default: True)
      --network-idle / --no-network-idle          Wait for network idle (default: False)
      --real-chrome/--no-real-chrome              If you have a Chrome browser installed on your device, enable this, and the Fetcher will launch an instance of your browser and use it. (default: False)
      --timeout INTEGER                           Timeout in milliseconds (default: 30000)
      --wait INTEGER                              Additional wait time in milliseconds after page load (default: 0)
      -s, --css-selector TEXT                     CSS selector to extract specific content from the page. It returns all matches.
      --wait-selector TEXT                        CSS selector to wait for before proceeding
      --hide-canvas / --show-canvas               Add noise to canvas operations (default: False)
      --proxy TEXT                                Proxy URL in format "http://username:password@host:port"
      -H, --extra-headers TEXT                    Extra headers in format "Key: Value" (can be used multiple times)
      --help                                      Show this message and exit.
    ```

## When to use each command

If you are not a Web Scraping expert and can't decide what to choose, you can use the following formula to help you decide:

- Use **`get`** with simple websites, blogs, or news articles
- Use **`fetch`** with modern web apps, or sites with dynamic content
- Use **`stealthy-fetch`** with protected sites, Cloudflare, or anti-bot systems

## Legal and Ethical Considerations

⚠️ **Important Guidelines:**

- **Check robots.txt**: Visit `https://website.com/robots.txt` to see scraping rules
- **Respect rate limits**: Don't overwhelm servers with requests
- **Terms of Service**: Read and comply with website terms
- **Copyright**: Respect intellectual property rights
- **Privacy**: Be mindful of personal data protection laws
- **Commercial use**: Ensure you have permission for business purposes

---

*Happy scraping! Remember to always respect website policies and comply with all applicable laws and regulations.*
