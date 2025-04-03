from pathlib import Path
import os


def get_cache_dir(environment_variable: str, default_subdirectory: str) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    default_path = repo_root / default_subdirectory

    path_str = os.environ.get(environment_variable, str(default_path))
    path = Path(path_str)
    path.mkdir(parents=True, exist_ok=True)

    return path
