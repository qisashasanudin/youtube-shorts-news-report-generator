#!/usr/bin/env python3
"""
Web Search Fallback Tool
Primary: Nous gateway (web_search)
Fallback: Local browser (browser_navigate + browser_snapshot on Bing)
"""

import json
import re
from typing import Optional

# Error patterns that trigger fallback
FALLBACK_TRIGGERS = [
    r"billing error",
    r"insufficient.*funds",
    r"payment required",
    r"charge authorization failed",
    r"402",
    r"timeout",
    r"ERR_CONNECTION_TIMED_OUT",
    r"ERR_NETWORK_CHANGED",
]


def should_fallback(error_msg: str) -> bool:
    """Check if error should trigger fallback to browser."""
    error_lower = error_msg.lower()
    return any(re.search(pattern, error_lower) for pattern in FALLBACK_TRIGGERS)


def format_bing_results(snapshot: str, limit: int = 5) -> list[dict]:
    """Extract structured results from Bing search snapshot."""
    results = []
    lines = snapshot.split('\n')
    
    current = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for result patterns in snapshot
        # Pattern: "- link \"domain.com\" [ref=eXX]"
        # Pattern: "- heading \"Title\" [level=2, ref=eYY]"
        # Pattern: "- paragraph\n  - StaticText \"Snippet...\""
        
        if 'link "' in line and 'ref=' in line:
            # Extract URL/domain
            match = re.search(r'link\s+"([^"]+)"\s+\[ref=', line)
            if match:
                if current:
                    results.append(current)
                current = {'url': '', 'title': '', 'snippet': '', 'source': 'bing'}
                domain = match.group(1)
                current['url'] = f"https://{domain}" if not domain.startswith('http') else domain
                
        elif 'heading "' in line and 'level=2' in line:
            match = re.search(r'heading\s+"([^"]+)"\s+\[level=2', line)
            if match and current:
                current['title'] = match.group(1)
                
        elif 'StaticText "' in line and 'paragraph' in '\n'.join(lines[max(0, lines.index(line)-2):lines.index(line)+1]):
            match = re.search(r'StaticText\s+"([^"]+)"', line)
            if match and current and not current['snippet']:
                current['snippet'] = match.group(1)[:300]
    
    if current:
        results.append(current)
    
    return results[:limit]


def search_web(query: str, limit: int = 5, hermes_tools=None) -> dict:
    """
    Search web with fallback.
    
    Args:
        query: Search query
        limit: Max results
        hermes_tools: Tool namespace with web_search, browser_navigate, browser_snapshot
    
    Returns:
        {"results": [...], "source": "nous|browser", "fallback_used": bool}
    """
    if hermes_tools is None:
        # When called from execute_code, tools are available via hermes_tools import
        from hermes_tools import web_search, browser_navigate, browser_snapshot
        hermes_tools = type('Tools', (), {
            'web_search': web_search,
            'browser_navigate': browser_navigate,
            'browser_snapshot': browser_snapshot
        })()
    
    # --- Try Nous gateway first ---
    try:
        result = hermes_tools.web_search(query=query, limit=limit)
        if result.get('success') and result.get('data', {}).get('web'):
            web_results = result['data']['web']
            formatted = []
            for r in web_results[:limit]:
                formatted.append({
                    'title': r.get('title', ''),
                    'url': r.get('url', ''),
                    'snippet': r.get('description', '')[:300],
                    'source': 'nous'
                })
            return {
                'success': True,
                'results': formatted,
                'source': 'nous',
                'fallback_used': False
            }
        elif result.get('error') and should_fallback(str(result.get('error', ''))):
            # Trigger fallback
            pass
        else:
            # Other error or empty results
            pass
    except Exception as e:
        if should_fallback(str(e)):
            pass  # Trigger fallback
        else:
            return {'success': False, 'error': f'Nous search failed: {e}', 'fallback_used': False}
    
    # --- Fallback: Local browser on Bing ---
    try:
        search_url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
        nav_result = hermes_tools.browser_navigate(url=search_url)
        
        if not nav_result.get('success'):
            return {'success': False, 'error': f'Browser navigation failed: {nav_result.get("error")}', 'fallback_used': True}
        
        # Wait a bit for results to load
        import time
        time.sleep(2)
        
        snap_result = hermes_tools.browser_snapshot(full=True)
        if not snap_result.get('success'):
            return {'success': False, 'error': f'Browser snapshot failed: {snap_result.get("error")}', 'fallback_used': True}
        
        snapshot = snap_result.get('snapshot', '')
        results = format_bing_results(snapshot, limit)
        
        if not results:
            return {'success': False, 'error': 'No results extracted from Bing', 'fallback_used': True}
        
        for r in results:
            r['source'] = 'browser'
        
        return {
            'success': True,
            'results': results,
            'source': 'browser',
            'fallback_used': True
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Browser fallback failed: {e}', 'fallback_used': True}


if __name__ == '__main__':
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else 'test query'
    result = search_web(query)
    print(json.dumps(result, indent=2))