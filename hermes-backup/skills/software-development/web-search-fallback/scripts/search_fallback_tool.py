#!/usr/bin/env python3
"""
Web Search Fallback Tool - Hermes Tool Registration
Copy this file to ~/.hermes/hermes-agent/tools/search_fallback.py
Then restart Hermes or run /reload in session.
"""

import json
import os
import sys

# Add scripts directory to path for imports
SKILL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts')
sys.path.insert(0, SKILL_DIR)

from tools.registry import registry
from search_fallback import search_web, should_fallback


def check_requirements() -> bool:
    """Check if either Nous gateway or local browser is available."""
    try:
        from hermes_config import get_config
        config = get_config()
        
        # Nous gateway enabled
        nous_ready = config.get('web', {}).get('use_gateway', False)
        
        # Local browser CDP configured
        browser_ready = bool(config.get('browser', {}).get('cdp_url'))
        
        return nous_ready or browser_ready
    except Exception:
        # If config check fails, assume available
        return True


def search_web_tool(query: str, limit: int = 5, task_id: str = None) -> str:
    """
    Hermes tool handler for search_web.
    
    Args:
        query: Search query string
        limit: Maximum results to return (default 5)
        task_id: Internal task ID
    
    Returns:
        JSON string with results
    """
    try:
        from hermes_tools import web_search, browser_navigate, browser_snapshot
        
        class Tools:
            web_search = staticmethod(web_search)
            browser_navigate = staticmethod(browser_navigate)
            browser_snapshot = staticmethod(browser_snapshot)
        
        result = search_web(query=query, limit=limit, hermes_tools=Tools)
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            'success': False,
            'error': f'Tool execution failed: {str(e)}',
            'fallback_used': False
        }, ensure_ascii=False)


# Register the tool
registry.register(
    name='search_web',
    toolset='web',
    schema={
        'name': 'search_web',
        'description': 'Search the web with automatic fallback: tries Nous gateway first, falls back to local browser on billing/timeout errors',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'Search query'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'Maximum number of results (default 5)',
                    'default': 5,
                    'minimum': 1,
                    'maximum': 20
                }
            },
            'required': ['query']
        }
    },
    handler=search_web_tool,
    check_fn=check_requirements,
    requires_env=[]
)