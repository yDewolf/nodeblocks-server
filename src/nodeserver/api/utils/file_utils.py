from pathlib import Path


def get_project_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / '.git').exists():
            return parent
    
    return Path(__file__).parent
