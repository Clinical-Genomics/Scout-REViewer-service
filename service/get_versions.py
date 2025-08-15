import subprocess

from dotenv import dotenv_values

def get_version(cmd_path) -> str:
    """Return version string."""
    cmd = [
        cmd_path,
        "--version"
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, check=True)
    return result.stdout.decode("utf-8")

def get_versions() -> str:
    """Return version strings."""
    env = dotenv_values(".env")

    return "\n".join(
        [ get_version(env.get("REV_PATH")),
          get_version(env.get("TRGT_PATH"))
        ])
