# X/Twitter Crypto Trending Monitoring (no API key)

## Technique: Chrome Cookie Extraction + Playwright Injection

Since X API requires OAuth setup, this technique uses the user's existing Chrome login session to browse X.com via Playwright — no API key needed.

## Prerequisites

- User has X.com logged in on Chrome
- Playwright MCP server is running
- `browser-cookie3` and `cryptography` Python packages installed

## Workflow

### Step 1: Extract X.com cookies from Chrome

```python
import browser_cookie3, json

cj = browser_cookie3.chrome(domain_name='x.com')
cookies = []
for c in cj:
    cookies.append({'name': c.name, 'value': c.value, 'domain': c.domain})
# Key cookies needed: auth_token, ct0, twid
```

Key cookies extracted:
- `auth_token`: The authentication token (most important)
- `ct0`: CSRF token required for API requests
- `twid`: User ID (u%3D... format)
- `personalization_id`: Session identifier

### Step 2: Inject into Playwright via MCP

```javascript
// Use mcp_playwright_browser_run_code_unsafe
await page.context().addCookies([
  {name: 'auth_token', value: '...', domain: '.x.com', path: '/'},
  {name: 'ct0', value: '...', domain: '.x.com', path: '/'},
  {name: 'twid', value: '...', domain: '.x.com', path: '/'},
  {name: 'personalization_id', value: '...', domain: '.x.com', path: '/'}
]);
await page.goto('https://x.com/home');
// Now logged in — check document.querySelector('[data-testid="primaryColumn"]')
```

### Step 3: Search for crypto topics

```javascript
await page.goto('https://x.com/search?q=crypto&f=live');
// Extract tweets:
const tweets = Array.from(document.querySelectorAll('[data-testid="tweet"]'))
  .map(t => t.querySelector('[data-testid="tweetText"]')?.textContent);
```

### Step 4: Cron job setup for regular monitoring

Create a cron job with `enabled_toolsets: ["browser"]` that:

1. Opens https://x.com via `mcp_playwright_browser_navigate`
2. Injects cookies via `mcp_playwright_browser_run_code_unsafe` with `page.context().addCookies()`
3. Searches crypto keywords: solana, BSC/BNB, memecoin, bitcoin + Chinese terms
4. Extracts trending topics + tweets
5. Summarizes and delivers to user

**IMPORTANT:** Cron sessions are FRESH — they have no prior browser state. The cookie values MUST be hardcoded in the cron job prompt string. When cookies expire (~30 days), re-extract and update the cron job.

**Recommended search keywords:**
- English: "solana", "binance", "BSC", "BNB", "memecoin", "crypto", "bitcoin"
- Chinese: "新币", "财富密码", "百倍", "冲", "上车", "打狗", "链上"
- KOL shill: "gem", "early", "next 100x", "smart money", "alpha"
- Event-driven: (dynamic — add based on current news)

## New Narrative Detection Flow

When user says "XXX现在很火" and GMGN shows nothing:

1. First run: `gmgn-cli market trenches --chain sol --limit 30` with grep for the keyword
2. If still nothing, run X search for the term + "crypto" via Playwright
3. Check if posts are < 1h old = narrative just starting
4. Tell user the event trigger, add keyword to cron job

### Example — Robinhood (2026-07-09)

- User: "robinhood链现在很火"
- GMGN: No $HOOD tokens anywhere
- X search: Robinhood filed "Time To Do Crypto" trademark
- Conclusion: Narrative < 1h old, chain tokens not minted yet
- Action: Add "robinhood" + "hood" to cron keywords, watch next 24h

### Example — CZ Final Form Bull (2026-07-04)

- User: Interested in CZ tokens
- GMGN: Multiple CZ-branded tokens on BSC
- X search: CZ-related KOL narratives driving the BSC counterpart tokens
- Conclusion: Established narrative, evaluate individual tokens for quality

## Cookie Refresh Strategy

When cookies expire (~30 days), re-extract from Chrome:

```bash
# On the user's machine where Chrome has X.com logged in
pip install browser-cookie3 cryptography --break-system-packages
python3 -c "
import browser_cookie3
cj = browser_cookie3.chrome(domain_name='x.com')
for c in cj:
    if c.name in ('auth_token','ct0','twid','personalization_id'):
        print(f'{c.name}={c.value}')
"
```

Then update the cron job prompt with the new cookie values.

## Pitfalls

- ⚠️ **Cookies expire ~30 days** — Monitor cron job output for auth failures; re-extract when it stops working
- ⚠️ **Cron jobs need cookie values hardcoded in prompt** — cron sessions don't have access to Chrome's cookie store. Always embed cookie values in the cron job prompt itself
- ⚠️ **Rate limiting** — X may rate-limit the Playwright session if too many requests. Keep searches to 3-5 keywords per run
- ⚠️ **`mcp_playwright_browser_run_code_unsafe`** is the ONLY tool that can run arbitrary JS including `addCookies()`. `browser_console` can evaluate expressions but cannot set cookies
- ⚠️ **Detection** — Playwright without stealth may trigger X bot detection. If login fails, user may need to log in directly in the Playwright browser once (via browser_navigate to X, manual login, then cookie extraction)
- ⚠️ **Empty search results** don't mean failure — check `document.body.innerText` to see if the page loaded. Sometimes X shows "Nothing to see" instead of actual results for new accounts
