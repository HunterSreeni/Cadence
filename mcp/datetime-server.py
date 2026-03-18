#!/usr/bin/env python3
"""Minimal MCP server that provides current date and time."""

from datetime import datetime
import zoneinfo

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("datetime")


@mcp.tool()
def get_current_datetime(timezone: str = "Asia/Kolkata") -> str:
    """Get the current date, time, and day of the week.

    Args:
        timezone: IANA timezone name (default: Asia/Kolkata / IST)
    """
    try:
        tz = zoneinfo.ZoneInfo(timezone)
    except (KeyError, zoneinfo.ZoneInfoNotFoundError):
        return f"Unknown timezone: {timezone}. Use IANA format like Asia/Kolkata, UTC, US/Eastern."

    now = datetime.now(tz)
    return (
        f"Date: {now.strftime('%A, %d %B %Y')}\n"
        f"Time: {now.strftime('%I:%M:%S %p')} ({now.strftime('%H:%M:%S')})\n"
        f"Timezone: {timezone} (UTC{now.strftime('%z')})\n"
        f"ISO: {now.isoformat()}"
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
