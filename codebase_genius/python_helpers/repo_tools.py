"""Repo tools: cloning, file tree building, README summarization.

These functions are invoked from Jac walkers via py_module integration.
"""
from __future__ import annotations
import os
import re
import json
import shutil
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from urllib.parse import urlparse
from .llm import summarize_readme_llm  # LLM optional summarizer
from git import Repo, GitCommandError  # type: ignore

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    ".mypy_cache",
}
TEXT_README_CANDIDATES = ["README.md", "README.rst", "README.txt"]


def validate_repo_url(repo_url: str) -> Dict[str, Any]:
    """Validate repository URL format and accessibility.
    
    Returns:
        dict with 'valid': bool, 'error': str (if invalid), 'normalized_url': str
    """
    if not repo_url or not isinstance(repo_url, str):
        return {"valid": False, "error": "URL must be a non-empty string"}
    
    # Normalize URL
    url = repo_url.strip().rstrip("/")
    
    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        return {"valid": False, "error": f"Invalid URL format: {e}"}
    
    # Check for supported hosts
    supported_hosts = ["github.com", "gitlab.com", "bitbucket.org"]
    if parsed.netloc not in supported_hosts:
        return {
            "valid": False, 
            "error": f"Unsupported host: {parsed.netloc}. Supported: {', '.join(supported_hosts)}"
        }
    
    # GitHub-specific validation
    if parsed.netloc == "github.com":
        # Expected format: https://github.com/owner/repo or https://github.com/owner/repo.git
        path_parts = [p for p in parsed.path.split("/") if p]
        if len(path_parts) < 2:
            return {
                "valid": False,
                "error": "GitHub URL must be in format: https://github.com/owner/repo"
            }
        
        owner, repo = path_parts[0], path_parts[1]
        if not re.match(r"^[\w.-]+$", owner) or not re.match(r"^[\w.-]+$", repo.replace(".git", "")):
            return {
                "valid": False,
                "error": f"Invalid owner/repo name: {owner}/{repo}"
            }
        
        # Normalize to https://github.com/owner/repo (remove .git)
        normalized = f"https://github.com/{owner}/{repo.replace('.git', '')}"
        return {"valid": True, "normalized_url": normalized}
    
    # Generic validation for other hosts
    return {"valid": True, "normalized_url": url}


 
@dataclass
class FileNode:
    path: str
    type: str  # 'file' or 'dir'
    children: Optional[List['FileNode']] = None

    def to_dict(self) -> Dict[str, Any]:
        children = None
        if self.children:
            children = [c.to_dict() for c in self.children]
        return {
            "path": self.path,
            "type": self.type,
            "children": children,
        }


def clone_repo(
    repo_url: str,
    base_dir: Optional[str] = None,
    retries: int = 2,
    backoff: float = 2.0,
) -> str:
    """Clone repo with shallow depth and retry logic.
    Returns path; raises RuntimeError on failure.
    """
    # Validate URL first
    validation = validate_repo_url(repo_url)
    if not validation["valid"]:
        raise ValueError(f"Invalid repository URL: {validation['error']}")
    
    repo_url = validation["normalized_url"]
    
    target_base = base_dir or tempfile.mkdtemp(prefix="codegenius_")
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    dest = os.path.join(target_base, repo_name)
    last_err: Optional[Exception] = None
    
    for attempt in range(retries + 1):
        try:
            if os.path.exists(dest):
                # Attempt pull instead of reclone
                repo = Repo(dest)
                repo.remotes.origin.pull()
                return dest
            Repo.clone_from(repo_url, dest, depth=1)
            return dest
        except GitCommandError as e:
            last_err = e
            # Check for common errors
            if "Authentication failed" in str(e) or "could not read Username" in str(e):
                raise RuntimeError(f"Private repository or authentication required: {repo_url}")
            elif "Repository not found" in str(e) or "not found" in str(e).lower():
                raise RuntimeError(f"Repository not found: {repo_url}")
            
            if os.path.exists(dest):
                shutil.rmtree(dest, ignore_errors=True)
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
            else:
                raise RuntimeError(
                    f"Git clone failed after {retries+1} attempts: {e}"
                )
        except Exception as e:
            last_err = e
            if os.path.exists(dest):
                shutil.rmtree(dest, ignore_errors=True)
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
            else:
                raise RuntimeError(
                    f"Git clone failed after {retries+1} attempts: {e}"
                )
    raise RuntimeError(f"Unreachable clone loop: {last_err}")


def build_file_tree(root_path: str) -> Dict[str, Any]:
    root = Path(root_path)

    def walk(p: Path) -> FileNode:
        if p.is_dir():
            if p.name in IGNORE_DIRS:
                return None  # type: ignore
            children: List[FileNode] = []
            for child in sorted(
                p.iterdir(), key=lambda x: (x.is_file(), x.name.lower())
            ):
                node = walk(child)
                if node:
                    children.append(node)
            return FileNode(
                path=str(p.relative_to(root)),
                type="dir",
                children=children,
            )
        else:
            return FileNode(path=str(p.relative_to(root)), type="file")

    tree = walk(root)
    return tree.to_dict() if tree else {}


def read_readme(root_path: str) -> Optional[str]:
    for candidate in TEXT_README_CANDIDATES:
        rp = Path(root_path) / candidate
        if rp.exists():
            try:
                return rp.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                return None
    return None


def summarize_readme(text: str, max_len: int = 500) -> str:
    """Summarize README using LLM if enabled, else naive fallback."""
    return summarize_readme_llm(text, max_len)


def repo_map_workflow(repo_url: str) -> Dict[str, Any]:
    try:
        path = clone_repo(repo_url)
        file_tree = build_file_tree(path)
        readme_text = read_readme(path) or ""
        summary = summarize_readme(readme_text)
        priority_files = find_important_files(file_tree)
        return {
            "repo_path": path,
            "file_tree": file_tree,
            "readme_summary": summary,
            "priority_files": priority_files,
            "error": None,
        }
    except Exception as e:
        return {
            "repo_path": "",
            "file_tree": {},
            "readme_summary": "",
            "priority_files": [],
            "error": f"repo_map_failed: {e}",
        }


def find_important_files(file_tree: Dict[str, Any]) -> List[str]:
    """Identify high-priority files for analysis (main.py, app.py, etc.)."""
    important = []
    priority_names = {
        "main.py",
        "app.py",
        "__main__.py",
        "__init__.py",
        "cli.py",
        "server.py",
        "run.py",
        "manage.py",
    }

    def search(tree: Dict[str, Any]) -> None:
        if not tree:
            return
        if tree.get("type") == "file":
            path = tree.get("path", "")
            fname = Path(path).name
            if fname in priority_names:
                important.append(path)
        if tree.get("children"):
            for child in tree["children"]:
                search(child)

    search(file_tree)
    return important


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("repo_url")
    args = ap.parse_args()
    result = repo_map_workflow(args.repo_url)
    print(json.dumps(result, indent=2))
