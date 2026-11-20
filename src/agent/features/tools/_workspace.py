from agent.core.config import WORKSPACE


def safe_workspace_path(path: str):

    file_path = (WORKSPACE / path).resolve()

    if not file_path.is_relative_to(WORKSPACE):

        raise ValueError("Access outside workspace is not allowed.")

    return file_path
