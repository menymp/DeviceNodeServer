import os

def get_secret(env_var: str, default: str = None) -> str:
    """
    Retrieve a secret value in a Docker-friendly way.

    1. If ENV_VAR is set, return its value.
    2. If ENV_VAR_FILE is set, read the file and return its contents.
    3. Otherwise, return default.

    Example:
        DB_PASSWORD or DB_PASSWORD_FILE
    """
    # Direct environment variable
    value = os.getenv(env_var)
    if value:
        return value

    # File-based secret convention
    file_var = f"{env_var}_FILE"
    file_path = os.getenv(file_var)
    if file_path and os.path.exists(file_path):
        with open(file_path) as f:
            return f.read().strip()

    # Fallback
    return default
