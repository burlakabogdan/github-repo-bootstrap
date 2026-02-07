
import sys
import os
import subprocess
import re
import questionary
from rich.console import Console
from utils import load_config, get_github_client, get_current_repo

console = Console()
config = load_config()

def get_current_branch():
    try:
        return subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
    except:
        return None

def main():
    console.print("[bold blue]Create Pull Request[/]")
    g = get_github_client()
    repo = get_current_repo(g)
    user = g.get_user()
    
    branch = get_current_branch()
    if not branch or branch == "main": # or default branch
        console.print("[red]Cannot create PR from default branch or detached head.[/]")
        sys.exit(1)
        
    # 1. Push Branch
    console.print(f"Current branch: [green]{branch}[/]")
    if questionary.confirm("Push current branch?").ask():
        with console.status("Pushing..."):
            try:
                subprocess.run(["git", "push", "-u", "origin", branch], check=True)
            except subprocess.CalledProcessError:
                console.print("[red]Failed to push branch.[/]")
                sys.exit(1)
    
    # 2. Extract Issue ID
    conf = config.get('commit_assistant', {})
    pattern = conf.get('branch_issue_pattern', r'^(feat|fix|chore|docs|refactor)\/(?P<id>\d+)(-.+)?$')
    match = re.search(pattern, branch)
    issue_id = match.group("id") if match else None
    
    # 3. Detect Template
    # List .github/PULL_REQUEST_TEMPLATE.md or .github/PULL_REQUEST_TEMPLATE/*.md
    # For MVP, just simple body or try to read file
    body = ""
    template_path = ".github/PULL_REQUEST_TEMPLATE.md" # naive check
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            body = f.read()
            
    if issue_id:
        # Append or replace link
        link_text = f"\n\nFixes #{issue_id}"
        if "Fixes #" not in body:
            body += link_text
            
    # 4. Input Details
    git_last_commit = subprocess.check_output(["git", "log", "-1", "--pretty=%s"], text=True).strip()
    
    title = questionary.text("PR Title:", default=git_last_commit).ask()
    
    # Allow editing body?
    # questionary definition of "editor" might be useful if installed
    # For now just simple text or skip
    # body = questionary.text("PR Body:", default=body).ask() # Multiline?
    
    if questionary.confirm("Create PR?").ask():
        with console.status("Creating PR..."):
            try:
                pr = repo.create_pull(
                    title=title,
                    body=body,
                    head=branch,
                    base=repo.default_branch
                )
                console.print(f"[bold green]PR Created: {pr.html_url}[/]")
                
                # 5. Project Status Update?
                # Trigger via GraphQL if needed. 
                # Ideally, GitHub Actions handles this, but we can do it manually.
                # PR is also an Item.
                # Logic: pr.raw_data['node_id'] -> add to project -> set status "Review"
                
                # 5. Project Status Update
                proj_conf = config.get('projects_v2', {})
                if proj_conf.get('enabled'):
                    try:
                        from bootstrap import ensure_project_v2
                        from project_utils import set_project_item_status, add_item_to_project, find_project_item_by_content
                        
                        # Use repository name if title is not specified
                        project_title = proj_conf.get('title') or repo.name
                        console.print(f"Adding PR to project '{project_title}'...")
                        
                        proj_action = ensure_project_v2(user.login, project_title)
                        
                        project_id = None
                        if proj_action['type'] == 'EXISTS':
                            project_id = proj_action['id']
                        elif proj_action['type'] == 'CREATE':
                            result = proj_action['action']()
                            project_id = result['id']
                            
                        if project_id:
                            # 1. Add PR to Project & Set Ready
                            item_id = add_item_to_project(project_id, pr.raw_data['node_id'])
                            set_project_item_status(project_id, item_id, "Ready")
                            
                            # 2. Update Linked Issue to Review
                            if issue_id:
                                try:
                                    linked_issue = repo.get_issue(int(issue_id))
                                    linked_item_id = find_project_item_by_content(project_id, linked_issue.raw_data['node_id'])
                                    if linked_item_id:
                                        set_project_item_status(project_id, linked_item_id, "Review")
                                        console.print(f"[green]Moved linked issue #{issue_id} to Review[/]")
                                    else:
                                         console.print(f"[yellow]Linked issue #{issue_id} not found in project.[/]")
                                except Exception as e:
                                    console.print(f"[yellow]Failed to update linked issue: {e}[/]")
                                    
                    except Exception as e:
                        console.print(f"[red]Failed to update project: {e}[/]")
                        
            except Exception as e:
                console.print(f"[red]Failed to create PR: {e}[/]")

if __name__ == "__main__":
    main()
