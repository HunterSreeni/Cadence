"""
Example cadence plugin.

Drop .py files in the commands/ folder to add custom /commands.
Each file must have a register() function that returns a dict
mapping command strings to handler functions.

Handler signature: handler(text: str, config: dict) -> str
"""


def register():
    """Return a dict of {"/command": handler_function}."""
    return {
        "/hello": handle_hello,
    }


def handle_hello(text, config):
    """Example command — responds with a greeting."""
    name = config.get("user", {}).get("name", "there")
    return f"\U0001f44b Hey {name}! This is an example plugin."
