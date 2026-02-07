
import sys
import re
import subprocess
import questionary
from rich.console import Console
from utils import load_config, get_github_client, get_current_repo

console = Console()
config = load_config()

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def main():
    console.print("[bold blue]Create Branch from Issue[/]")
    
    # 1. Fetch Issues
    try:
        g = get_github_client()
        repo = get_current_repo(g)
    except Exception as e:
        console.print(f"[red]Failed to connect: {e}[/]")
        sys.exit(1)
    
    try:
        # Convert iterator to list to get actual issues
        issues_list = list(repo.get_issues(state='open'))
        
        # Filter out pull requests (GitHub API returns PRs as issues)
        issues_only = [i for i in issues_list if not i.pull_request]
        
        if not issues_only:
            console.print("[yellow]No open issues found.[/]")
            sys.exit(0)
            
        issue_map = {f"#{i.number} {i.title}": i for i in issues_only}
    except Exception as e:
        console.print(f"[red]Failed to fetch issues: {e}[/]")
        sys.exit(1)
        
    choice = questionary.select(
        "Select Issue:",
        choices=list(issue_map.keys())
    ).ask()
    
    if not choice:
        console.print("Cancelled.")
        sys.exit(0)
    
    issue = issue_map[choice]
    
    # 2. Generate Name
    # Default prefix: feature? user choice?
    # Helper wizard.
    branch_type = questionary.select(
        "Branch Type:",
        choices=["feat", "fix", "chore", "docs", "refactor"]
    ).ask()
    
    slug = slugify(issue.title)
    # limit slug length?
    if len(slug) > 50: slug = slug[:50].strip('-')
    
    branch_name = f"{branch_type}/{issue.number}-{slug}"
    
    console.print(f"Proposed branch: [green]{branch_name}[/]")
    
    if questionary.confirm("Create and checkout?").ask():
        try:
            subprocess.run(["git", "checkout", "-b", branch_name], check=True)
            console.print(f"[bold green]Switched to branch {branch_name}[/]")
        except subprocess.CalledProcessError:
            console.print("[red]Failed to create branch (maybe it exists?)[/]")
    else:
        console.print("Cancelled.")

if __name__ == "__main__":
    main()
