import logging
import sys
from mcp.server.fastmcp import FastMCP

# Minimal logging to stderr
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
mcp = FastMCP("Test Server")

@mcp.tool()
def echo(text: str) -> str:
    return f"Echo: {text}"

if __name__ == "__main__":
    mcp.run()
