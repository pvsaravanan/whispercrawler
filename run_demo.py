from whispercrawler import Crawler

# Fetch a page using the speedy HTTP/3 static crawler
print("Fetching quotes.toscrape.com...")
page = Crawler.get("https://quotes.toscrape.com/")

# Use CSS selectors to extract quotes
quotes = page.css(".quote")
print(f"Found {len(quotes)} quotes on the page!\n")

# Print the first three quotes
for i, quote in enumerate(quotes[:10], 1):
    text = quote.css(".text::text").get()
    author = quote.css(".author::text").get()
    print(f"Quote {i}: {text}")
    print(f"Author {i}: {author}")
    print("-" * 40)
