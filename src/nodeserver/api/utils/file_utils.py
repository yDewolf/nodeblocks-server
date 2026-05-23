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
    _project_root: Path = Path()

    @property
    def project_root(cls):
        return cls._project_root

    @project_root.setter
    def project_root(cls, new_root: Path):
        cls._project_root = new_root
        logger.info(f"Set PROJECT ROOT to {cls._project_root}")
    
    @classmethod
    def select_project_root(cls):
        repos = get_git_repos()
        for idx, repo_path in enumerate(repos):
            print(f"[{idx}]-{repo_path}")
        
        idx = -1
        while idx < 0 or idx > len(repos):
            idx = int(input("Select which repository should be the project root: "))
            if not idx < 0 and not idx > len(repos):
                selected_path = repos[idx]
        
        cls.project_root = selected_path

def get_project_root():
    return FileUtils.project_root