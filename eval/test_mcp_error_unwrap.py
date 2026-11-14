"""Checks that mcp_client.call_tool keeps a tool's own error message when anyio wraps it
in nested exception groups (the criterion 3 bug). No MCP server or API key needed.

    python eval/test_mcp_error_unwrap.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import mcp_client  # noqa: E402

try:
    Group = ExceptionGroup                   # Python 3.11+, like the real thing
    def group(msg, errs):
        return ExceptionGroup(msg, errs)
except NameError:                            # Python 3.10: stand-in with the same .exceptions shape
    class Group(Exception):
        def __init__(self, msg, errs):
            super().__init__(msg)
            self.exceptions = tuple(errs)
    def group(msg, errs):
        return Group(msg, errs)


def run(raiser):
    async def fake(name, arguments):
        raise raiser()
    mcp_client._call = fake
    try:
        mcp_client.call_tool("search_listings", {})
    except mcp_client.MCPError as e:
        return str(e)
    raise AssertionError("no MCPError raised")


tool_msg = ("The tool 'search_listings' returned an error: Error executing tool search_listings: "
            "Unknown search strategy 'semantic'. Choose one of: keyword, category.")

# 1. tool error wrapped in two nested groups -> its own text, no server-won't-start advice
msg = run(lambda: group("unhandled errors in a TaskGroup", [group("unhandled errors in a TaskGroup",
                                                                  [mcp_client.MCPError(tool_msg)])]))
assert "keyword, category" in msg and "Check that mcp_server.py" not in msg, msg
print("PASS  tool error survives two nested exception groups")

# 2. a bare MCPError still passes straight through
msg = run(lambda: mcp_client.MCPError(tool_msg))
assert msg == tool_msg
print("PASS  bare MCPError unchanged")

# 3. a real transport failure inside a group keeps the advice and now names the cause
msg = run(lambda: group("unhandled errors in a TaskGroup", [OSError("server exited")]))
assert "OSError: server exited" in msg and "Check that mcp_server.py runs" in msg, msg
print("PASS  transport failure still gets the 'check the server' advice, with the real cause")
