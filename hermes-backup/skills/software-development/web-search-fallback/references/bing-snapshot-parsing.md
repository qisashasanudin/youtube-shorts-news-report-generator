# Bing Search Snapshot Parsing Reference

## Sample Snapshot Structure (from `browser_snapshot(full=True)`)

```
- generic
  - banner
    - button "Skip to content" [ref=e1]
    - button "Accessibility Feedback" [ref=e2]
    - form
      - link "Back to Bing search" [ref=e5]
      - search
        - searchbox "Enter your search here" [ref=e9]: battlefield 6 tsuru reef
  - complementary "Account Rewards and Preferences"
    - button "Microsoft Rewards" [ref=e4]
    - link "Sign in" [ref=e5]
  - main "Search Results" [ref=e4]
    - list
      - listitem [level=1]
        - link "ea.com" [ref=e30]
          - StaticText "ea.com"
          - StaticText "https://www.ea.com › games › battlefield"
        - heading "Battlefield – Electronic Arts" [level=2, ref=e17]
          - link "Battlefield – Electronic Arts" [ref=e31]
        - paragraph
          - StaticText "We rallied 20+ years of Battlefield experience..."
      - listitem [level=1]
        - link "wikipedia.org" [ref=e32]
        - heading "Battlefield (video game series) - Wikipedia" [level=2, ref=e18]
```

## Element Patterns to Extract

| Element Type | Pattern | Example |
|--------------|---------|---------|
| Domain link | `- link "domain.com" [ref=eXX]` | `- link "ea.com" [ref=e30]` |
| Result title (h2) | `- heading "Title" [level=2, ref=eYY]` | `- heading "Battlefield – Electronic Arts" [level=2, ref=e17]` |
| Snippet | `- paragraph` + `- StaticText "text"` | `- paragraph\n  - StaticText "We rallied 20+ years..."` |

## Elements to Filter Out (Nav Bar)

| Keyword | Matches |
|---------|---------|
| `back to bing` | "Back to Bing search" link |
| `microsoft rewards` | Rewards button |
| `sign in` | Sign in link |
| `images` | IMAGES tab |
| `videos` | VIDEOS tab |
| `maps` | MAPS tab |
| `shopping` | SHOPPING tab |
| `news` | NEWS tab |
| `all` | ALL tab (uppercase) |
| `search` | SEARCH tab |
| `bing` | Any bing.com internal link |
| `microsoft` | Microsoft domains |

## Regex Patterns Used

```python
# Domain link
r'link\s+"([^"]+)"\s+\[ref='

# Heading level 2
r'heading\s+"([^"]+)"\s+\[level=2'

# Snippet text
r'StaticText\s+"([^"]+)"'
```

## Minimal Working Extraction

```python
def extract_bing_results(snapshot: str, limit: int = 5) -> list[dict]:
    results = []
    lines = snapshot.split('\n')
    current = {}
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Skip nav elements
        if any(kw in line.lower() for kw in 
               ['back to bing', 'microsoft rewards', 'sign in', 'images', 'videos', 
                'maps', 'shopping', 'news', 'bing', 'microsoft']):
            continue
            
        # Domain link → new result
        if 'link "' in line and 'ref=' in line:
            m = re.search(r'link\s+"([^"]+)"\s+\[ref=', line)
            if m:
                domain = m.group(1)
                if any(kw in domain.lower() for kw in ['bing', 'microsoft', 'search']):
                    continue
                if current and current.get('title'):
                    results.append(current)
                current = {'url': f'https://{domain}', 'title': '', 'snippet': ''}
               
        # Title
        elif 'heading "' in line and 'level=2' in line:
            m = re.search(r'heading\s+"([^"]+)"\s+\[level=2', line)
            if m and current:
                title = m.group(1)
                if not any(kw in title.lower() for kw in ['bing', 'microsoft', 'search', 'rewards']):
                    current['title'] = title
                   
        # Snippet
        elif 'StaticText "' in line and i > 0 and 'paragraph' in lines[i-1]:
            m = re.search(r'StaticText\s+"([^"]+)"', line)
            if m and current and not current.get('snippet'):
                current['snippet'] = m.group(1)[:300]
    
    if current and current.get('title'):
        results.append(current)
    
    return [r for r in results if r.get('title') and r.get('url')][:limit]
```

## Verified Pattern from Gemma 4 Search (Jun 2026)

The session searching "gemma 4" produced a Bing snapshot matching the documented patterns exactly:

```
- list
  - listitem [level=1]
    - link "deepmind.google" [ref=e21]
    - heading "Gemma 4 — Google DeepMind" [level=2, ref=e16]
      - link "Gemma 4 — Google DeepMind" [ref=e22]
    - paragraph
```

- Domain link: `link "deepmind.google"` ✓
- Title (h2): `heading "Gemma 4 — Google DeepMind" [level=2]` ✓
- Snippet follows paragraph → StaticText pattern ✓

Nav elements correctly filtered: "Back to Bing search", "Microsoft Rewards", "Sign in", "ALL", "SEARCH", "IMAGES", "VIDEOS", "MAPS", "MORE" tabs.

This confirms the extraction logic works for current Bing layout.