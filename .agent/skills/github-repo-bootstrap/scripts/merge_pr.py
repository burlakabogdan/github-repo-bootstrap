
import sys
import re
import questionary
from rich.console import Console
from rich.table import Table
from utils import load_config, get_github_client, get_current_repo

console = Console()
config = load_config()

def main():
    console.print("[bold blue]Merge Pull Request[/]")
    
    try:
        g = get_github_client()
        repo = get_current_repo(g)
    except Exception as e:
        console.print(f"[red]Failed to initialize GitHub client: {e}[/]")
        sys.exit(1)
    
    # 1. List Open PRs
    try:
        prs = list(repo.get_pulls(state='open'))
    except Exception as e:
        console.print(f"[red]Failed to fetch PRs: {e}[/]")
        sys.exit(1)
    
    if not prs:
        console.print("[yellow]No open PRs found.[/]")
        sys.exit(0)
    
    # Display PRs in a table
    table = Table(title="Open Pull Requests")
    table.add_column("#", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Author", style="magenta")
    table.add_column("Reviews", style="yellow")
    table.add_column("Mergeable", style="blue")
    
    for pr in prs:
        # Get review status
        reviews = list(pr.get_reviews())
        approved = any(r.state == "APPROVED" for r in reviews)
        review_status = "✓ Approved" if approved else "⏳ Pending"
        
        # Check if mergeable
        mergeable = "✓" if pr.mergeable else "✗"
        
        table.add_row(
            str(pr.number),
            pr.title,
            pr.user.login,
            review_status,
            mergeable
        )
    
    console.print(table)
    
    # 2. Select PR
    pr_choices = [f"#{pr.number} - {pr.title}" for pr in prs]
    selected = questionary.select("Select PR to merge:", choices=pr_choices).ask()
    
    if not selected:
        sys.exit(0)
    
    pr_number = int(selected.split(" - ")[0].replace("#", ""))
    pr = next((p for p in prs if p.number == pr_number), None)
    
    if not pr:
        console.print("[red]PR not found.[/]")
        sys.exit(1)
    
    console.print(f"\n[bold]Merging PR #{pr.number}:[/] {pr.title}")
    console.print(f"[dim]Branch: {pr.head.ref} → {pr.base.ref}[/]")
    
    # 3. Check if mergeable
    if not pr.mergeable:
        console.print("[red]⚠ PR is not mergeable (conflicts or checks failed)[/]")
        if not questionary.confirm("Continue anyway?").ask():
            sys.exit(0)
    
    # 4. Choose merge method
    merge_methods = [
        "merge - Create a merge commit",
        "squash - Squash and merge",
        "rebase - Rebase and merge"
    ]
    
    method_choice = questionary.select("Merge method:", choices=merge_methods).ask()
    
    if not method_choice:
        sys.exit(0)
    
    merge_method = method_choice.split(" - ")[0]
    
    # 5. Confirm merge
    console.print(f"\n[bold]Merge Summary:[/]")
    console.print(f"  PR: #{pr.number} - {pr.title}")
    console.print(f"  Method: [cyan]{merge_method}[/]")
    console.print(f"  Branch: {pr.head.ref} → {pr.base.ref}")
    
    if not questionary.confirm("Proceed with merge?").ask():
        console.print("[yellow]Merge cancelled.[/]")
        sys.exit(0)
    
    # 6. Merge PR
    try:
        with console.status("Merging PR..."):
            pr.merge(merge_method=merge_method)
        console.print(f"[bold green]✓ PR #{pr.number} merged successfully![/]")
        
        # 6a. Switch to base branch and pull
        try:
             import subprocess
             base_branch = pr.base.ref
             console.print(f"Switching to [green]{base_branch}[/] and updating...")
             subprocess.run(["git", "checkout", base_branch], check=True)
             subprocess.run(["git", "pull"], check=True)
        except Exception as e:
             console.print(f"[yellow]Failed to switch/update branch: {e}[/]")
        
        # 7. Delete branch (optional)
        if questionary.confirm(f"Delete branch '{pr.head.ref}'?", default=True).ask():
            try:
                ref = repo.get_git_ref(f"heads/{pr.head.ref}")
                ref.delete()
                console.print(f"[green]✓ Branch '{pr.head.ref}' deleted.[/]")
            except Exception as e:
                console.print(f"[yellow]Could not delete branch: {e}[/]")
        
        # 8. Extract and close linked issue
        # Look for "Fixes #123" or "Closes #123" in PR body
        if pr.body:
            issue_pattern = r'(?:Fixes|Closes|Resolves)\s+#(\d+)'
            matches = re.findall(issue_pattern, pr.body, re.IGNORECASE)
            
            if matches:
                issue_num = int(matches[0])
                console.print(f"[dim]Found linked issue #{issue_num}[/]")
                
                # Issue will be auto-closed by GitHub if using "Fixes #" keyword
                # But we can update project status manually if needed
                
            # 9. Update Project Status
            proj_conf = config.get('projects_v2', {})
            if proj_conf.get('enabled'):
                 try:
                     from bootstrap import ensure_project_v2
                     from project_utils import set_project_item_status, find_project_item_by_content
                     
                     project_title = proj_conf.get('title') or repo.name
                     console.print(f"Updating project '{project_title}' status...")
                     
                     proj_action = ensure_project_v2(g.get_user().login, project_title)
                     
                     project_id = None
                     if proj_action['type'] == 'EXISTS':
                         project_id = proj_action['id']
                     elif proj_action['type'] == 'CREATE':
                         result = proj_action['action']()
                         project_id = result['id']
                         
                     if project_id:
                         # Update PR Status
                         pr_item_id = find_project_item_by_content(project_id, pr.raw_data['node_id'])
                         if pr_item_id:
                             set_project_item_status(project_id, pr_item_id, "Done")
                             console.print(f"[green]Set PR #{pr.number} status to Done[/]")
                         
                         # Update Linked Issue Status
                         if matches:
                             issue_num = int(matches[0])
                             try:
                                 linked_issue = repo.get_issue(issue_num)
                                 issue_item_id = find_project_item_by_content(project_id, linked_issue.raw_data['node_id'])
                                 if issue_item_id:
                                     set_project_item_status(project_id, issue_item_id, "Done")
                                     console.print(f"[green]Set Issue #{issue_num} status to Done[/]")
                             except Exception as e:
                                 console.print(f"[yellow]Failed to update linked issue: {e}[/]")
                 except Exception as e:
                     console.print(f"[yellow]Failed to update project status: {e}[/]")

    except Exception as e:
        console.print(f"[red]Failed to merge PR: {e}[/]")
        sys.exit(1)

if __name__ == "__main__":
    main()
