# Concrete Rails Pagination + Slow-Query Audit Workflow

## When to use
Use this probe when `rails notes` is unavailable or inadequate because Rails is not in the bundle path, and a quick offline audit is needed for pagination, backtraces, and slow queries.

## Probe pattern
1. Start with the nearest-practical path candidate.
2. If it is not a valid Rails root, fall back one degree at a time to the project root.
3. Stop as soon as a usable root is found; do not keep relaxing the heuristic.

Rails root fallback policy:
- Prefer directories that contain `Gemfile`, `config/routes.rb`, `app/models`, and `log/`.
- If multiple candidates exist, choose the one that best matches the user's active application path.

## Minimum checks
- If `app/models` is missing and the user expected a Rails app, report the mismatch immediately.
- Log paths should match the active Rails environment.
- Backtrace-suppression/pagination checks should compare candidate paths before opening files.
- Limit slow-query search to `log/*.log`.
- Use content_search `target=content`, not filename matching, for slow queries.

## Output expectation
- Identify the correct Rails root from the above heuristic.
- Report any missing Rails conventions or log paths.
- Provide concrete paths and findings, not assumed defaults.