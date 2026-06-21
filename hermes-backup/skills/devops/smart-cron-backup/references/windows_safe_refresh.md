# Windows Safe Refresh Pattern

When refreshing a destination directory in-place on Windows, direct deletion of a locked or read-only tree can fail after the old data is already removed, leaving the destination empty. Use this safer replacement pattern:

1. Copy the source into a temp directory under the destination root.
2. Attempt to remove/replace the destination tree.
   - If removal fails, move the old destination to a `.bak` sibling when possible.
   - Then move the temp tree into the destination location.
3. If promotion fails still, emit a warning instead of fatally exiting.
4. After successful promotion, prune any unexpected stale siblings.

This preserves backups when Windows filesystem locking would otherwise clobber the tree during refresh.
