#!/usr/bin/env python3
"""
Dynamic Tool Registration Script
Run this in a Hermes session to register the search_web tool dynamically.
Usage: exec(open("~/.hermes/skills/software-development/web-search-fallback/scripts/register_tool.py").read())
"""

import os
import sys

# Add skill scripts to path
SKILL_DIR = os.path.expanduser("~/.hermes/skills/software-development/web-search-fallback")
SCRIPTS_DIR = os.path.join(SKILL_DIR, 'scripts')
sys.path.insert(0, SCRIPTS_DIR)

# Import and execute the tool registration
exec(open(os.path.join(SCRIPTS_DIR, 'search_fallback_tool.py')).read())

print("✓ search_web tool registered dynamically")
print("  Primary: Nous gateway (web_search)")
print("  Fallback: Local browser (browser_navigate + browser_snapshot)")
print("  Triggers: billing errors, timeouts, network errors")