"""Service settings.

Settings are read from environment variables, so they can be set with e.g.
`docker run -e` or a compose `env_file`. Values in a `.env` file in the working
directory are used as defaults for anything not already set in the environment.
"""

import os

from dotenv import load_dotenv

load_dotenv(".env", override=False)


def get_setting(name: str) -> str | None:
    """Return a setting, e.g. REV_PATH, or None if it is not set."""
    return os.environ.get(name)
