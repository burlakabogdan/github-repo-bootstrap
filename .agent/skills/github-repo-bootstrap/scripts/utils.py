import os
import sys
import yaml
import json
from pathlib import Path
from typing import Optional, Dict, Any

from github import Github, Auth
from rich.console import Console
from rich.panel import Panel

console = Console()

CONFIG_PATH = Path("../assets/config.yml")
REPO_CONFIG_PATH = Path(".github/repo-skill.yml")

def load_config() -> Dict[str, Any]:
    """Load config from repo override or default asset."""
    # 1. Check repo-local config
    if REPO_CONFIG_PATH.exists():
        try:
            with open(REPO_CONFIG_PATH, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to load local config: {e}. Using default.[/]")

    # 2. Check default asset config (relative to script location)
    script_dir = Path(__file__).parent
    default_config = script_dir.parent / "assets" / "config.yml"
    
    if default_config.exists():
        with open(default_config, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
            
    # 3. Fallback
    console.print("[red]Error: No configuration found![/]")
    sys.exit(1)

def get_github_client() -> Github:
    """Initialize GitHub client from token."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        # Try finding via gh cli
        import shutil
        import subprocess
        
        if shutil.which("gh"):
            try:
                token = subprocess.check_output(["gh", "auth", "token"], text=True).strip()
                os.environ["GITHUB_TOKEN"] = token
            except subprocess.CalledProcessError:
                pass
                
    if not token:
        console.print(Panel("[red]GITHUB_TOKEN not found![/]\nPlease export GITHUB_TOKEN or login with `gh auth login`.", title="Authentication Error"))
        sys.exit(1)
        
    auth = Auth.Token(token)
    return Github(auth=auth)

class RepositoryNotFoundError(Exception):
    """Raised when local git repository is not found or has no remote."""
    pass

def get_current_repo(g: Github, raise_error: bool = False):
    """Detect current repository from git remote."""
    import subprocess
    try:
        remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        # Parse owner/repo from URL
        # e.g., https://github.com/owner/repo.git or git@github.com:owner/repo.git
        if "github.com" not in remote_url:
            if raise_error:
                raise RepositoryNotFoundError("Not a GitHub repository remote.")
            console.print("[red]Not a GitHub repository remote.[/]")
            sys.exit(1)
            
        clean_url = remote_url.replace(".git", "")
        if "http" in clean_url:
            parts = clean_url.split("github.com/")[-1].split("/")
        else:
            parts = clean_url.split(":")[-1].split("/")
            
        owner = parts[0]
        repo_name = parts[1]
        
        return g.get_repo(f"{owner}/{repo_name}")
    except Exception as e:
        if raise_error:
            raise RepositoryNotFoundError(f"Failed to detect repository: {e}")
        console.print(f"[red]Failed to detect repository: {e}[/]")
        sys.exit(1)
