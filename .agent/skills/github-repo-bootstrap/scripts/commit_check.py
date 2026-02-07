
import sys
import re
import subprocess
import questionary
from rich.console import Console
from utils import load_config, get_github_client, get_current_repo

console = Console()
config = load_config()

def get_current_branch():
    try:
        # Using show-current is safer in empty repos than rev-parse HEAD
        return subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
    except subprocess.CalledProcessError:
        return None

def check_staged_changes():
    """Check if there are any changes staged for commit."""
    try:
        # git diff --cached --quiet returns 1 if there are changes, 0 if not
        result = subprocess.run(["git", "diff", "--cached", "--quiet"])
        return result.returncode != 0
    except Exception:
        return False

def parse_issue_from_branch(branch_name, pattern):
    match = re.match(pattern, branch_name)
    if match:
        return match.group("id")
    return None

def main():
    console.print("[bold blue]Commit Assistant[/]")
    
    # 1. Config & Branch
    conf = config.get('commit_assistant', {})
    
    # Check for staged changes first
    if not check_staged_changes():
        console.print("[yellow]No changes staged for commit.[/]")
        if questionary.confirm("Would you like to stage all changes (git add .)?").ask():
            subprocess.run(["git", "add", "."])
        else:
            console.print("[red]Aborting. Please stage changes before using Commit Assistant.[/]")
            sys.exit(0)

    branch = get_current_branch()
    issue_id = None
    
    if branch:
        pattern = conf.get('branch_issue_pattern', r'^(feat|fix|chore|docs|refactor)\/(?P<id>\d+)(-.+)?$')
        issue_id = parse_issue_from_branch(branch, pattern)
        if issue_id:
            console.print(f"Detected Issue ID from branch: [green]#{issue_id}[/]")

    # 2. Interactive Prompts
    types = conf.get('allowed_types', ["feat", "fix", "chore"])
    
    commit_type = questionary.select("Type:", choices=types).ask()
    if not commit_type: sys.exit(0)
    
    scope = questionary.text("Scope (optional):").ask()
    subject = questionary.text("Subject:", validate=lambda text: len(text) >= 5 or "Subject must be at least 5 chars").ask()
    
    if not issue_id:
        if conf.get('enforce_issue_link', True):
            # Fetch open issues
            try:
                g = get_github_client()
                repo = get_current_repo(g)
                # Convert iterator to list
                issues_list = list(repo.get_issues(state='open'))
                # Filter out pull requests
                issues_only = [i for i in issues_list if not i.pull_request]
                choices = [f"#{i.number} {i.title}" for i in issues_only]
            except Exception as e:
                console.print(f"[red]Failed to fetch issues: {e}[/]")
                choices = []
            
            if choices:
                sel = questionary.select("Select Issue:", choices=choices).ask()
                if sel:
                    issue_id = sel.split(" ")[0].replace("#", "")
            else:
                 issue_id = questionary.text("Issue ID:").ask()

    # 3. Generate Message
    # Format: "{type}({scope}): {subject} #{issue}"
    fmt = conf.get('commit_format', "{type}({scope}): {subject} #{issue}")
    
    scope_part = scope if scope else ""
    # Adjust format if scope is empty to avoid empty parens ()
    if not scope:
        if "{type}({scope})" in fmt:
            fmt = fmt.replace("{type}({scope})", "{type}")
            
    msg = fmt.format(type=commit_type, scope=scope_part, subject=subject, issue=issue_id)
    
    console.print(f"\n[bold]Preview:[/]\n{msg}\n")
    
    if questionary.confirm("Commit with this message?").ask():
        subprocess.run(["git", "commit", "-m", msg])
    else:
        console.print("Cancelled.")

if __name__ == "__main__":
    main()
