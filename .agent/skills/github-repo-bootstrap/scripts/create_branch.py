
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
            
            # --- Auto-update Issue Status ---
            try:
                from bootstrap import ensure_project_v2
                from project_utils import set_project_item_status, find_project_item_by_content
                
                user = g.get_user()
                proj_conf = config.get('projects_v2', {})
                if proj_conf.get('enabled'):
                    project_title = proj_conf.get('title') or repo.name
                    
                    console.print(f"Updating issue status in project '{project_title}'...")
                    proj_action = ensure_project_v2(user.login, project_title)
                    
                    project_id = None
                    if proj_action['type'] == 'EXISTS':
                        project_id = proj_action['id']
                    elif proj_action['type'] == 'CREATE':
                        result = proj_action['action']()
                        project_id = result['id']
                        
                    if project_id:
                        # Find issue item in project
                        item_id = find_project_item_by_content(project_id, issue.raw_data['node_id'])
                        if item_id:
                            set_project_item_status(project_id, item_id, "In Progress")
                        else:
                            console.print("[yellow]Issue not found in project.[/]")
            except Exception as e:
                console.print(f"[yellow]Failed to update issue status: {e}[/]")
            # -------------------------------
            
        except subprocess.CalledProcessError:
            console.print("[red]Failed to create branch (maybe it exists?)[/]")
    else:
        console.print("Cancelled.")

if __name__ == "__main__":
    main()
