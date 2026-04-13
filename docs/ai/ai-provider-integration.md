# AI Provider Integration Guide

This comprehensive guide shows how to integrate WhisperCrawler with major AI providers including OpenAI, Anthropic, Google Gemini, and OpenRouter. WhisperCrawler offers multiple integration approaches: direct Python API usage, MCP Server integration, and custom wrapper implementations.

## Table of Contents

- [Integration Approaches](#integration-approaches)
- [OpenAI Integration](#openai-integration)
- [Anthropic Claude Integration](#anthropic-claude-integration)  
- [Google Gemini Integration](#google-gemini-integration)
- [OpenRouter Integration](#openrouter-integration)
- [MCP Server Integration](#mcp-server-integration)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Integration Approaches

WhisperCrawler provides three main approaches for AI integration:

### 1. **Direct Python API Integration**
Use WhisperCrawler as a Python library within your AI application for maximum control and customization.

### 2. **MCP Server Integration**
Leverage WhisperCrawler's Model Context Protocol (MCP) server for seamless integration with AI chatbots and agents.

### 3. **HTTP API Wrapper**
Create custom HTTP endpoints that combine WhisperCrawler with your preferred AI provider.

## OpenAI Integration

### Direct Python API Integration

```python
import asyncio
from openai import AsyncOpenAI
from whispercrawler import Selector, DynamicFetcher
from whispercrawler.core.shell import Convertor

class WhisperCrawlerOpenAI:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.convertor = Convertor()
    
    async def scrape_and_analyze(
        self, 
        url: str, 
        prompt: str,
        css_selector: str = None,
        model: str = "gpt-4o-mini"
    ) -> str:
        """Scrape content and send to OpenAI for analysis"""
        
        # Scrape the content
        response = await DynamicFetcher.async_fetch(url)
        selector = Selector(response.content, url=response.url)
        
        # Extract specific content if CSS selector provided
        if css_selector:
            elements = selector.css(css_selector)
            content = "\n".join([elem.text for elem in elements])
        else:
            content = selector.text
        
        # Convert to markdown for better AI processing
        markdown_content = self.convertor.to_markdown(content)
        
        # Send to OpenAI
        completion = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes web content."},
                {"role": "user", "content": f"Content from {url}:\n\n{markdown_content}\n\nTask: {prompt}"}
            ],
            max_tokens=1000
        )
        
        return completion.choices[0].message.content

# Usage Example
async def main():
    scraper = WhisperCrawlerOpenAI(api_key="your-openai-api-key")
    
    result = await scraper.scrape_and_analyze(
        url="https://news.ycombinator.com",
        prompt="Summarize the top 5 stories",
        css_selector=".storylink"
    )
    print(result)

# Run the example
asyncio.run(main())
```

### Batch Processing with OpenAI

```python
import asyncio
from typing import List, Dict
from openai import AsyncOpenAI
from whispercrawler.fetchers.chrome import AsyncDynamicSession

class BatchOpenAIProcessor:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def process_multiple_urls(
        self, 
        url_prompts: List[Dict[str, str]],
        model: str = "gpt-4o-mini"
    ) -> List[str]:
        """Process multiple URLs with different prompts in parallel"""
        
        # Scrape all URLs in parallel
        async with AsyncDynamicSession() as session:
            scraping_tasks = [
                session.fetch(item["url"]) for item in url_prompts
            ]
            responses = await asyncio.gather(*scraping_tasks)
        
        # Process with OpenAI in parallel
        ai_tasks = []
        for i, response in enumerate(responses):
            selector = Selector(response.content, url=response.url)
            content = selector.text[:4000]  # Limit content for token management
            
            task = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": f"Content: {content}\n\nTask: {url_prompts[i]['prompt']}"}
                ]
            )
            ai_tasks.append(task)
        
        ai_responses = await asyncio.gather(*ai_tasks)
        return [resp.choices[0].message.content for resp in ai_responses]

# Usage
async def main():
    processor = BatchOpenAIProcessor(api_key="your-api-key")
    
    url_prompts = [
        {"url": "https://example1.com", "prompt": "Extract key insights"},
        {"url": "https://example2.com", "prompt": "Find contact information"},
        {"url": "https://example3.com", "prompt": "Summarize main topics"}
    ]
    
    results = await processor.process_multiple_urls(url_prompts)
    for i, result in enumerate(results):
        print(f"Result for {url_prompts[i]['url']}:\n{result}\n")

asyncio.run(main())
```

## Anthropic Claude Integration

### Direct API Integration

```python
import asyncio
from anthropic import AsyncAnthropic
from whispercrawler import Selector
from whispercrawler.fetchers.stealth_chrome import AsyncStealthySession

class WhisperCrawlerClaude:
    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)
    
    async def stealth_scrape_and_analyze(
        self, 
        url: str, 
        prompt: str,
        css_selector: str = None,
        model: str = "claude-3-5-sonnet-20241022"
    ) -> str:
        """Use stealth scraping for protected sites with Claude analysis"""
        
        # Use stealth fetcher for anti-bot bypass
        async with AsyncStealthySession(
            impersonate="chrome",
            anti_detection=True
        ) as session:
            response = await session.fetch(url)
        
        selector = Selector(response.content, url=response.url)
        
        # Extract content with CSS selector if provided
        if css_selector:
            elements = selector.css(css_selector)
            content = "\n".join([elem.text for elem in elements])
        else:
            content = selector.text
        
        # Limit content to manage tokens (Claude has high context limits)
        content = content[:100000]  # Claude can handle large contexts
        
        # Send to Claude
        message = await self.client.messages.create(
            model=model,
            max_tokens=4000,
            messages=[{
                "role": "user", 
                "content": f"I scraped this content from {url}:\n\n{content}\n\n{prompt}"
            }]
        )
        
        return message.content[0].text

# Advanced usage with adaptive parsing
class AdaptiveClaudeProcessor:
    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)
    
    async def adaptive_content_extraction(
        self, 
        url: str, 
        target_content_description: str,
        model: str = "claude-3-5-sonnet-20241022"
    ) -> Dict[str, str]:
        """Use Claude to identify and extract specific content dynamically"""
        
        # First, get the full page
        response = await AsyncStealthySession.async_fetch(url)
        selector = Selector(response.content, url=response.url)
        
        # Get page structure for Claude to analyze
        page_structure = selector.css("*").text[:10000]
        
        # Ask Claude to identify the best CSS selector
        selector_message = await self.client.messages.create(
            model=model,
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"""Analyze this HTML page structure and provide a CSS selector to extract: {target_content_description}

Page content preview:
{page_structure}

Respond with only the CSS selector, nothing else."""
            }]
        )
        
        css_selector = selector_message.content[0].text.strip()
        
        # Extract content using the identified selector
        try:
            target_elements = selector.css(css_selector)
            extracted_content = "\n".join([elem.text for elem in target_elements])
            
            return {
                "selector_used": css_selector,
                "extracted_content": extracted_content,
                "url": url
            }
        except Exception as e:
            return {
                "error": f"Failed to extract with selector {css_selector}: {str(e)}",
                "fallback_content": selector.text[:5000],
                "url": url
            }

# Usage
async def main():
    processor = AdaptiveClaudeProcessor(api_key="your-anthropic-api-key")
    
    result = await processor.adaptive_content_extraction(
        url="https://news.ycombinator.com",
        target_content_description="article titles and their scores"
    )
    print(result)

asyncio.run(main())
```

## Google Gemini Integration

### Using Google's Generative AI

```python
import asyncio
import google.generativeai as genai
from whispercrawler import Selector, DynamicFetcher
from whispercrawler.core.shell import Convertor

class WhisperCrawlerGemini:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        self.convertor = Convertor()
    
    async def scrape_and_generate(
        self, 
        url: str, 
        prompt: str,
        css_selector: str = None,
        output_format: str = "markdown"
    ) -> str:
        """Scrape content and process with Gemini"""
        
        # Scrape content
        response = await DynamicFetcher.async_fetch(url)
        selector = Selector(response.content, url=response.url)
        
        # Extract specific elements if selector provided
        if css_selector:
            elements = selector.css(css_selector)
            if output_format == "markdown":
                content = self.convertor.to_markdown("\n".join([elem.outer_html for elem in elements]))
            else:
                content = "\n".join([elem.text for elem in elements])
        else:
            content = self.convertor.to_markdown(selector.outer_html) if output_format == "markdown" else selector.text
        
        # Process with Gemini
        full_prompt = f"""Content scraped from {url}:

{content}

Task: {prompt}"""
        
        response = await asyncio.to_thread(
            self.model.generate_content, full_prompt
        )
        
        return response.text

# Multi-modal processing with images
class GeminiMultiModalProcessor:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    async def analyze_page_with_images(
        self, 
        url: str, 
        prompt: str
    ) -> str:
        """Scrape page content and images for multi-modal analysis"""
        
        # Scrape page
        response = await DynamicFetcher.async_fetch(url)
        selector = Selector(response.content, url=response.url)
        
        # Extract text content
        text_content = selector.text
        
        # Extract image URLs
        images = selector.css("img")
        image_urls = [img.get("src") for img in images if img.get("src")]
        
        # For demonstration, we'll use the first image
        # In production, you might want to download and process multiple images
        image_url = image_urls[0] if image_urls else None
        
        if image_url:
            # Note: In practice, you'd download the image and convert to appropriate format
            content_parts = [
                f"Text content from {url}:\n{text_content}",
                f"Found image at: {image_url}",
                prompt
            ]
        else:
            content_parts = [f"Text content from {url}:\n{text_content}", prompt]
        
        response = await asyncio.to_thread(
            self.model.generate_content, content_parts
        )
        
        return response.text

# Usage
async def main():
    scraper = WhisperCrawlerGemini(api_key="your-gemini-api-key")
    
    result = await scraper.scrape_and_generate(
        url="https://example.com",
        prompt="Summarize the main points and create bullet points",
        css_selector="main, article",
        output_format="markdown"
    )
    print(result)

asyncio.run(main())
```

## OpenRouter Integration

### Universal API Access

```python
import asyncio
import aiohttp
from typing import Optional, List, Dict
from whispercrawler import Selector
from whispercrawler.fetchers.requests import AsyncFetcher

class WhisperCrawlerOpenRouter:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
    
    async def scrape_and_process(
        self, 
        url: str, 
        prompt: str,
        model: str = "anthropic/claude-3.5-sonnet",
        css_selector: Optional[str] = None,
        max_tokens: int = 1000
    ) -> str:
        """Scrape content and process with any OpenRouter model"""
        
        # Scrape content with impersonation
        response = await AsyncFetcher.async_fetch(
            url,
            impersonate="chrome",
            headers={"User-Agent": "Mozilla/5.0 (compatible; research bot)"}
        )
        
        selector = Selector(response.content, url=response.url)
        
        # Extract content
        if css_selector:
            elements = selector.css(css_selector)
            content = "\n".join([elem.text for elem in elements])
        else:
            content = selector.text
        
        # Limit content based on model context window
        content = self._limit_content_by_model(content, model)
        
        # Send to OpenRouter
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://your-app.com",  # Optional
                "X-Title": "WhisperCrawler Integration"  # Optional
            }
            
            data = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": f"Content from {url}:\n\n{content}\n\nTask: {prompt}"
                    }
                ],
                "max_tokens": max_tokens
            }
            
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            ) as resp:
                result = await resp.json()
                return result["choices"][0]["message"]["content"]
    
    def _limit_content_by_model(self, content: str, model: str) -> str:
        """Limit content based on model's context window"""
        # Simplified token estimation (4 chars ≈ 1 token)
        if "gpt-4" in model:
            max_chars = 100000  # ~25k tokens
        elif "claude-3" in model:
            max_chars = 400000  # ~100k tokens
        elif "gemini" in model:
            max_chars = 800000  # ~200k tokens
        else:
            max_chars = 12000   # ~3k tokens for smaller models
        
        return content[:max_chars]

# Batch processing with multiple models
class MultiModelProcessor:
    def __init__(self, api_key: str):
        self.openrouter = WhisperCrawlerOpenRouter(api_key)
    
    async def compare_models(
        self, 
        url: str, 
        prompt: str,
        models: List[str] = None
    ) -> Dict[str, str]:
        """Compare responses from different models"""
        
        if models is None:
            models = [
                "anthropic/claude-3.5-sonnet",
                "openai/gpt-4o-mini",
                "google/gemini-pro-1.5"
            ]
        
        tasks = []
        for model in models:
            task = self.openrouter.scrape_and_process(url, prompt, model)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return dict(zip(models, results))

# Usage
async def main():
    processor = WhisperCrawlerOpenRouter(api_key="your-openrouter-api-key")
    
    result = await processor.scrape_and_process(
        url="https://example.com",
        prompt="Extract the main topics and provide a summary",
        model="anthropic/claude-3.5-sonnet",
        css_selector="article, .content"
    )
    print(result)
    
    # Compare multiple models
    multi_processor = MultiModelProcessor(api_key="your-openrouter-api-key")
    comparisons = await multi_processor.compare_models(
        url="https://news.ycombinator.com",
        prompt="Summarize the top stories"
    )
    
    for model, response in comparisons.items():
        print(f"\n{model}:")
        print(response)

asyncio.run(main())
```

## MCP Server Integration

For seamless integration with AI chatbots and agents, use WhisperCrawler's MCP server:

### Setup for Claude Desktop

Add to your Claude Desktop configuration file:

```json
{
  "mcpServers": {
    "whispercrawler": {
      "command": "whispercrawler",
      "args": ["mcp"]
    }
  }
}
```

### Setup for Custom Applications

```python
import asyncio
from mcp.client import Client
from mcp.stdio import StdioTransport

async def use_whispercrawler_mcp():
    """Example of using WhisperCrawler MCP server programmatically"""
    
    # Start MCP client
    transport = StdioTransport(
        command=["whispercrawler", "mcp"]
    )
    
    async with Client(transport) as client:
        # List available tools
        tools = await client.list_tools()
        print("Available tools:", [tool.name for tool in tools])
        
        # Use the get tool for basic scraping
        result = await client.call_tool(
            name="get",
            arguments={
                "url": "https://example.com",
                "css_selector": "h1, h2, p",
                "output_format": "markdown"
            }
        )
        print("Scraped content:", result.content)

asyncio.run(use_whispercrawler_mcp())
```

## Best Practices

### 1. Token Management
```python
def optimize_content_for_ai(content: str, target_tokens: int = 3000) -> str:
    """Optimize content length for AI processing"""
    # Estimate tokens (rough: 4 characters = 1 token)
    estimated_tokens = len(content) // 4
    
    if estimated_tokens <= target_tokens:
        return content
    
    # Truncate content intelligently
    target_chars = target_tokens * 4
    
    # Try to break at paragraph boundaries
    paragraphs = content.split('\n\n')
    result = ""
    
    for paragraph in paragraphs:
        if len(result) + len(paragraph) <= target_chars:
            result += paragraph + '\n\n'
        else:
            break
    
    return result.strip()
```

### 2. Error Handling
```python
import logging
from typing import Union

async def robust_scrape_and_analyze(
    url: str, 
    ai_processor_func,
    max_retries: int = 3
) -> Union[str, Dict[str, str]]:
    """Robust scraping with retry logic and fallbacks"""
    
    for attempt in range(max_retries):
        try:
            # Try stealth fetcher first
            response = await AsyncStealthySession.async_fetch(url)
            selector = Selector(response.content, url=response.url)
            content = selector.text
            
            # Process with AI
            result = await ai_processor_func(content)
            return result
            
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            
            if attempt < max_retries - 1:
                # Fallback to regular fetcher
                try:
                    response = await AsyncDynamicSession.async_fetch(url)
                    selector = Selector(response.content, url=response.url)
                    content = selector.text
                    result = await ai_processor_func(content)
                    return result
                except Exception as fallback_error:
                    logging.warning(f"Fallback failed: {str(fallback_error)}")
                    continue
            else:
                return {
                    "error": f"Failed to scrape {url} after {max_retries} attempts",
                    "last_error": str(e)
                }
```

### 3. Content Preprocessing
```python
from whispercrawler.core.shell import Convertor

class ContentOptimizer:
    def __init__(self):
        self.convertor = Convertor()
    
    def prepare_content_for_ai(
        self, 
        selector: Selector,
        format_type: str = "markdown",
        remove_noise: bool = True
    ) -> str:
        """Optimize content for AI processing"""
        
        if remove_noise:
            # Remove script, style, and other noise elements
            selector.css("script, style, nav, footer, aside").remove()
        
        # Extract main content
        main_content = selector.css("main, article, .content, #content")
        
        if main_content:
            content_html = "\n".join([elem.outer_html for elem in main_content])
        else:
            content_html = selector.outer_html
        
        # Convert based on format preference
        if format_type == "markdown":
            return self.convertor.to_markdown(content_html)
        elif format_type == "text":
            return Selector(content_html).text
        else:
            return content_html
```

### 4. Rate Limiting and Caching

```python
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
import hashlib
import json

class RateLimitedAIProcessor:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests_log = []
        self.cache: Dict[str, Dict] = {}
        self.cache_duration = timedelta(hours=1)
    
    async def process_with_rate_limit(
        self, 
        url: str, 
        prompt: str,
        ai_processor_func
    ) -> str:
        """Process with rate limiting and caching"""
        
        # Check cache first
        cache_key = self._get_cache_key(url, prompt)
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if datetime.now() - cache_entry["timestamp"] < self.cache_duration:
                return cache_entry["result"]
        
        # Rate limiting
        await self._wait_for_rate_limit()
        
        # Process request
        result = await ai_processor_func(url, prompt)
        
        # Cache result
        self.cache[cache_key] = {
            "result": result,
            "timestamp": datetime.now()
        }
        
        return result
    
    def _get_cache_key(self, url: str, prompt: str) -> str:
        """Generate cache key from URL and prompt"""
        combined = f"{url}||{prompt}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    async def _wait_for_rate_limit(self):
        """Implement rate limiting"""
        now = datetime.now()
        
        # Remove old requests
        cutoff = now - timedelta(minutes=1)
        self.requests_log = [req_time for req_time in self.requests_log if req_time > cutoff]
        
        # Check if we're at the limit
        if len(self.requests_log) >= self.requests_per_minute:
            wait_time = 60 - (now - self.requests_log[0]).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        # Log this request
        self.requests_log.append(now)
```

## Troubleshooting

### Common Issues and Solutions

#### 1. **Content Too Large for AI Context Window**
```python
# Solution: Implement intelligent content chunking
def chunk_content_intelligently(content: str, chunk_size: int = 4000) -> List[str]:
    """Split content into semantic chunks"""
    paragraphs = content.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) <= chunk_size:
            current_chunk += paragraph + '\n\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + '\n\n'
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks
```

#### 2. **Anti-Bot Protection Blocking Scraping**
```python
# Solution: Use stealth mode with proper configuration
async def bypass_protection(url: str) -> str:
    """Handle anti-bot protection"""
    try:
        # Use stealth fetcher with anti-detection
        response = await AsyncStealthySession.async_fetch(
            url,
            anti_detection=True,
            stealth=True,
            impersonate="chrome"
        )
        return response.content
    except Exception:
        # Fallback to proxy rotation
        response = await AsyncStealthySession.async_fetch(
            url,
            proxies=["proxy1:port", "proxy2:port"]  # Add your proxies
        )
        return response.content
```

#### 3. **Memory Issues with Large-Scale Scraping**
```python
# Solution: Implement streaming processing
async def stream_process_urls(urls: List[str], ai_processor, batch_size: int = 10):
    """Process URLs in batches to manage memory"""
    results = []
    
    for i in range(0, len(urls), batch_size):
        batch = urls[i:i + batch_size]
        
        # Process batch
        batch_results = await asyncio.gather(*[
            ai_processor(url) for url in batch
        ], return_exceptions=True)
        
        results.extend(batch_results)
        
        # Optional: Clean up memory
        import gc
        gc.collect()
        
        # Optional: Add delay between batches
        await asyncio.sleep(1)
    
    return results
```

#### 4. **API Rate Limits**
```python
# Solution: Implement exponential backoff
import random

async def call_ai_with_backoff(ai_call_func, max_retries: int = 5):
    """Call AI API with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return await ai_call_func()
        except Exception as e:
            if "rate limit" in str(e).lower() and attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(wait_time)
                continue
            raise
    
    raise Exception(f"Failed after {max_retries} attempts")
```

### Debugging Tips

1. **Enable verbose logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **Monitor token usage**:
```python
def estimate_tokens(text: str) -> int:
    """Rough token estimation"""
    return len(text) // 4

def log_token_usage(content: str, model: str):
    tokens = estimate_tokens(content)
    print(f"Sending ~{tokens} tokens to {model}")
```

3. **Test with simple examples first**:
```python
# Start with a simple test
async def test_integration():
    response = await DynamicFetcher.async_fetch("https://httpbin.org/html")
    selector = Selector(response.content)
    content = selector.text[:1000]  # Limit content for testing
    print(f"Successfully scraped {len(content)} characters")

asyncio.run(test_integration())
```

## Conclusion

WhisperCrawler provides flexible integration options with all major AI providers. Choose the approach that best fits your use case:

- Use **direct API integration** for maximum control and custom workflows
- Use **MCP Server integration** for seamless chatbot integration
- Use **HTTP wrapper patterns** for microservice architectures

Remember to implement proper error handling, rate limiting, and content optimization for production deployments. The combination of WhisperCrawler's powerful scraping capabilities with AI analysis creates robust solutions for web data processing and analysis.
