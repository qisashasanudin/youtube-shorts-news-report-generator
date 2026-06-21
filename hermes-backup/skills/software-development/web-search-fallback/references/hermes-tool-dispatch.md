# Hermes Tool Dispatch Pattern Reference

## Critical: How Hermes Calls Tool Handlers

When you register a tool with `registry.register()`, the dispatcher (`tools/registry.py:dispatch`) calls your handler as:

```python
# Inside registry.dispatch()
return entry.handler(args, **kwargs)
```

**The first argument is ALWAYS an `args` dict** containing the schema parameters.
Additional kwargs (`task_id`, `session_id`, `user_task`, etc.) come as keyword arguments.

---

## ❌ Wrong Handler Signature

```python
def my_tool(query: str, limit: int = 5, task_id: str = None) -> str:
    ...
    
registry.register(name="my_tool", handler=my_tool, ...)
```

**Result**: `TypeError: my_tool() got multiple values for keyword argument 'task_id'`

Because the dispatcher calls: `my_tool({"query": "x", "limit": 5}, task_id="abc")`
→ Python sees `query` as positional dict AND keyword `task_id` → conflict.

---

## ✅ Correct Pattern: Dispatch Wrapper

```python
def my_tool_impl(query: str, limit: int = 5, task_id: str = None) -> str:
    """Actual implementation with clean signature."""
    ...

def my_tool_dispatch(args: dict, **kwargs) -> str:
    """Dispatcher-compatible wrapper."""
    query = args.get("query", "")
    limit = args.get("limit", 5)
    task_id = kwargs.pop("task_id", None)  # POP to avoid duplicate
    return my_tool_impl(query=query, limit=limit, task_id=task_id, **kwargs)

registry.register(name="my_tool", handler=my_tool_dispatch, ...)
```

**Key points:**
1. Wrapper takes `(args: dict, **kwargs)`
2. Extract schema params from `args.get()`
3. **`kwargs.pop("task_id", None)`** — remove from kwargs before passing to impl
4. Pass remaining `**kwargs` through for `session_id`, `user_task`, etc.

---

## Common Kwargs Passed by Hermes

| Kwarg | Source | Use Case |
|-------|--------|----------|
| `task_id` | Agent loop | Terminal/browser session isolation |
| `session_id` | Conversation | Session tracking |
| `user_task` | Agent loop | Browser snapshot context |
| `tool_call_id` | LLM call | Tool call correlation |
| `turn_id` | Conversation | Turn tracking |
| `api_request_id` | Request | API call correlation |

---

## Schema Definition Must Match Extraction

```python
schema = {
    "name": "my_tool",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "limit": {"type": "integer", "default": 5}
        },
        "required": ["query"]
    }
}
```

The `args` dict will have exactly these keys: `{"query": "...", "limit": 5}`

---

## Verification Test

```python
# Test the wrapper directly
result = my_tool_dispatch({"query": "test", "limit": 3}, task_id="test_123")
print(result)  # Should work without "multiple values" error
```