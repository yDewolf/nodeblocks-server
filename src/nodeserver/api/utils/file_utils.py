from typing import Optional
from pathlib import Path
import logging
logger = logging.getLogger("root")

def get_git_repos() -> list[Path]:
    git_repos: list[Path] = []
    for parent in Path(__file__).resolve().parents:
        if (parent / '.git').exists():
            git_repos.append(parent)
    
    return git_repos

class FileUtils:
    _project_root: Optional[Path] = None

    @classmethod
    def select_project_root(cls):
        repos = get_git_repos()
        for idx, repo_path in enumerate(repos):
            print(f"[{idx}]-{repo_path}")
        
        idx = -1
        while idx < 0 or idx > len(repos):
            idx = int(input("Select which repository should be the project root: "))
            if not idx < 0 and not idx > len(repos):
                cls.set_project_root(repos[idx])
                return

    @classmethod
    def set_project_root(cls, project_root: str | Path):
        cls._project_root = Path(project_root)
        logger.info(f"Set PROJECT ROOT to {cls._project_root}")

