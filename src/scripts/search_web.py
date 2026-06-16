import base64
import html
import re
import sys
import urllib.parse
import requests
from typing import List, Dict, Set

MAX_SEARCH_QUERY_LENGTH = 220
SEARCH_TIMEOUT_SECONDS = 20
BING_BASE_URL = "https://www.bing.com/search?q={query}"
YAHOO_BASE_URL = "https://search.yahoo.com/search?p={query}"

AUTHORITY_HOST_MARKERS = [
    "news", "press", "media", "times", "daily", "post",
    "journal", "broadcast", "tribune", "herald", "gazette",
    "insider", "bulletin", "reuters", "apnews", "bloomberg",
    "cnbc", "nytimes", "washingtonpost", "theguardian", "wsj"
]

AUTHORITY_TEXT_MARKERS = [
    "news", "press", "media", "report", "article", "official",
    "broadcast", "statement", "breaking", "journal", "daily",
    "times", "post", "tribune", "herald", "gazette", "insider",
    "bulletin", "announced", "revealed", "confirmed", "launch"
]

BLOCKED_DOMAINS = [
    "aliexpress", "alibaba", "amazon", "shop", "esquire",
    "ebay", "walmart", "bestbuy", "gamestop", "steam", "epicgames"
]

def sanitize_search_query(query: str) -> str:
    if not query:
        return ""
    normalized = query.replace("|", " ").replace("\u2014", "-").replace("\u2013", "-")
    normalized = normalized.replace("\u2018", "'").replace("\u2019", "'")
    normalized = normalized.replace("\u201c", '"').replace("\u201d", '"')
    normalized = re.sub(r"[^\x00-\x7F]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized

def normalize_search_query(query: str, max_length: int = MAX_SEARCH_QUERY_LENGTH) -> str:
    cleaned = " ".join(query.strip().split())
    if len(cleaned) <= max_length:
        return cleaned
    trimmed = cleaned[:max_length]
    return trimmed.rsplit(" ", 1)[0]

def strip_html_tags(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()

def query_variations(query: str) -> List[str]:
    normalized = query.strip()
    if not normalized:
        return []
    query_lower = normalized.lower()
    variations = [normalized]
    if "news" not in query_lower:
        variations.append(f"{normalized} news")
    source_hints = [
        "news", "official news", "press release",
        "news article", "media report", "breaking news",
    ]
    outlet_queries = [f"{normalized} {hint}" for hint in source_hints if hint not in query_lower]
    variations.extend(outlet_queries[:6])
    if len(normalized) < 150 and '"' not in normalized:
        variations.append(f'"{normalized}"')
    seen = set()
    unique = []
    for var in variations:
        cleaned = normalize_search_query(sanitize_search_query(var))
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            unique.append(cleaned)
    return unique

def is_authoritative_url(url: str) -> bool:
    if not url:
        return False
    parsed = urllib.parse.urlparse(url.lower())
    host = parsed.netloc
    if any(marker in host for marker in AUTHORITY_HOST_MARKERS):
        return True
    return False

def has_authority_markers(text: str) -> bool:
    if not text:
        return False
    return any(marker in text.lower() for marker in AUTHORITY_TEXT_MARKERS)

def is_blocked_url(url: str) -> bool:
    if not url:
        return True
    return any(blocked in url.lower() for blocked in BLOCKED_DOMAINS)

def score_search_result(item: Dict[str, str], query: str) -> int:
    title = (item.get("title") or "").lower()
    snippet = (item.get("snippet") or "").lower()
    url = (item.get("url") or "").lower()
    score = 0
    query_terms = set(re.findall(r"\w+", query.lower()))
    overlap = 0
    for term in query_terms:
        if len(term) < 3:
            continue
        if term in title or term in snippet:
            overlap += 1
    if is_authoritative_url(url):
        score += 18
    if has_authority_markers(url):
        score += 8
    if has_authority_markers(title) or has_authority_markers(snippet):
        score += 8
    if is_blocked_url(url):
        score -= 80
    score += min(overlap, 8) * 3
    return score

def decode_bing_redirect(href: str) -> str:
    # First unescape HTML entities
    href = href.replace("&amp;", "&")
    
    # Try u=a1 pattern (legacy)
    match = re.search(r"u=a1([^&]+)", href)
    if match:
        try:
            encoded = match.group(1)
            encoded += "=" * ((4 - len(encoded) % 4) % 4)
            return base64.urlsafe_b64decode(encoded).decode("utf-8")
        except Exception:
            pass
    
    # Try modern p= parameter pattern (contains base64 URL + tracking params)
    match = re.search(r"[?&]p=([^&]+)", href)
    if match:
        try:
            encoded = match.group(1)
            # The p param contains: base64_url + base64_timestamp_and_tracking
            # Split at the second base64 chunk (JmltdHM= = timestamp marker)
            if "JmltdHM" in encoded:
                url_part = encoded.split("JmltdHM")[0]
            else:
                url_part = encoded
            url_part += "=" * ((4 - len(url_part) % 4) % 4)
            return base64.urlsafe_b64decode(url_part).decode("utf-8")
        except Exception:
            pass
    
    return href

def decode_yahoo_redirect(href: str) -> str:
    match = re.search(r"RU=([^/]+)", href)
    if not match:
        return ""
    return urllib.parse.unquote(match.group(1))

def search_bing_html(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    if not query:
        return []
    url = BING_BASE_URL.format(query=urllib.parse.quote_plus(query))
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=SEARCH_TIMEOUT_SECONDS)
        resp.raise_for_status()
        html_text = resp.text
        results = []
        for match in re.finditer(
            r'<h2[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>\s*</h2>',
            html_text, re.IGNORECASE | re.DOTALL
        ):
            href = html.unescape(match.group(1))
            href = decode_bing_redirect(href)
            title = strip_html_tags(match.group(2))
            after = html_text[match.end(): match.end() + 400]
            snippet_match = re.search(r'<p[^>]*>(.*?)</p>', after, re.IGNORECASE | re.DOTALL)
            snippet = strip_html_tags(snippet_match.group(1)) if snippet_match else ""
            if title and href and not is_blocked_url(href):
                results.append({"title": title[:120], "snippet": snippet, "url": href})
            if len(results) >= max_results:
                break
        return results
    except Exception as e:
        print(f"[WARN] Bing HTML search failed: {e}", file=sys.stderr)
        return []

def search_yahoo_html(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    if not query:
        return []
    url = YAHOO_BASE_URL.format(query=urllib.parse.quote_plus(query))
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=SEARCH_TIMEOUT_SECONDS)
        resp.raise_for_status()
        html_text = resp.text
        results = []
        for anchor_match in re.finditer(
            r'(<a [^>]*target="_blank"[^>]*referrerpolicy="origin"[^>]*>.*?</a>)',
            html_text, re.IGNORECASE | re.DOTALL
        ):
            anchor = anchor_match.group(1)
            href_match = re.search(r'href="([^"]+)"', anchor)
            if not href_match:
                continue
            href = href_match.group(1)
            if "r.search.yahoo.com" not in href:
                continue
            url = decode_yahoo_redirect(href)
            if not url or "yahoo.com" in url or is_blocked_url(url):
                continue
            title_match = re.search(r'<h3[^>]*>(.*?)</h3>', anchor, re.IGNORECASE | re.DOTALL)
            title = strip_html_tags(title_match.group(1)) if title_match else ""
            snippet = ""
            after = html_text[anchor_match.end(): anchor_match.end() + 500]
            snippet_match = re.search(r'<div[^>]*class="compText[^"]*"[^>]*>.*?<p[^>]*>(.*?)</p>', after, re.IGNORECASE | re.DOTALL)
            if snippet_match:
                snippet = strip_html_tags(snippet_match.group(1))
            if title and len(title) > 5:
                results.append({"title": title[:120], "snippet": snippet, "url": url})
            if len(results) >= max_results:
                break
        return results
    except Exception as e:
        print(f"[WARN] Yahoo HTML search failed: {e}", file=sys.stderr)
        return []

def search_web(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    if not query or not query.strip():
        return []
    normalized = normalize_search_query(sanitize_search_query(query))
    if not normalized:
        return []
    queries = query_variations(normalized)
    all_results: List[Dict] = []
    seen_urls: Set[str] = set()
    for current_query in queries:
        search_results = search_bing_html(current_query, max_results * 2)
        if not search_results:
            search_results = search_yahoo_html(current_query, max_results * 2)
        for item in search_results:
            url = item.get("url")
            if not url or url in seen_urls or is_blocked_url(url):
                continue
            seen_urls.add(url)
            item_score = score_search_result(item, current_query)
            all_results.append({"score": item_score, **item})
    if not all_results:
        print(f"[WEB SEARCH] No results for: {normalized}")
        return []
    all_results.sort(key=lambda x: x["score"], reverse=True)
    ranked = [
        {"title": item["title"], "snippet": item["snippet"], "url": item["url"]}
        for item in all_results[:max_results]
    ]
    for idx, item in enumerate(ranked, 1):
        print(f"[WEB SEARCH] {idx}. {item['title']} -> {item['url']}")
    return ranked

if __name__ == "__main__":
    # Parse arguments: first arg is query, optional second arg is max_results
    if len(sys.argv) < 2:
        query = "latest gaming news"
        max_results = 5
    else:
        # Check if last argument is a number (max_results)
        if sys.argv[-1].isdigit():
            max_results = int(sys.argv[-1])
            query = " ".join(sys.argv[1:-1])
        else:
            max_results = 5
            query = " ".join(sys.argv[1:])
    results = search_web(query, max_results)
    print(f"Total results: {len(results)}")