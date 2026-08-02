# Sample Output

Sample extraction output from `whispercrawler extract`, captured from
<https://www.servicenow.com/> on 2026-08-02.

| File | Command | Size |
|---|---|---|
| `servicenow.html` | `extract get <url> servicenow.html` | 477 KB |
| `servicenow.md` | `extract get <url> servicenow.md` | 41.5 KB |
| `servicenow-body.md` | `extract get <url> servicenow-body.md -s "div.body-content-wrapper"` | 7.6 KB |

The output format follows the file extension (`.html` / `.md` / `.txt`).

The unscoped markdown is dominated by the site's mega-menu navigation; the scoped
version selects the AEM content region only. Note that `#main-content` — the target of
the page's own skip link — does not exist in the served HTML, so it selects nothing.

Content belongs to ServiceNow and is included only to illustrate extraction output.
