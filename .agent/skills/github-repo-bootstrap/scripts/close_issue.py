
import sys
import questionary
from rich.console import Console
from rich.table import Table
from utils import load_config, get_github_client, get_current_repo

console = Console()
config = load_config()

def main():
    console.print("[bold blue]Close Issue[/]")
    
    try:
        g = get_github_client()
        repo = get_current_repo(g)
    except Exception as e:
        console.print(f"[red]Failed to initialize GitHub client: {e}[/]")
        sys.exit(1)
    
    # 1. List Open Issues
    try:
        issues_list = list(repo.get_issues(state='open'))
        # Filter out pull requests
        issues = [i for i in issues_list if not i.pull_request]
    except Exception as e:
        console.print(f"[red]Failed to fetch issues: {e}[/]")
        sys.exit(1)
    
    if not issues:
        console.print("[yellow]No open issues found.[/]")
        sys.exit(0)
    
    # Display issues in a table
    table = Table(title="Open Issues")
    table.add_column("#", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Labels", style="magenta")
    table.add_column("Assignee", style="yellow")
    
    for issue in issues:
        labels = ", ".join([l.name for l in issue.labels]) if issue.labels else "-"
        assignee = issue.assignee.login if issue.assignee else "-"
        
        table.add_row(
            str(issue.number),
            issue.title[:50] + "..." if len(issue.title) > 50 else issue.title,
            labels,
            assignee
        )
    
    console.print(table)
    
    # 2. Select Issue
    issue_choices = [f"#{i.number} - {i.title}" for i in issues]
    selected = questionary.select("Select issue to close:", choices=issue_choices).ask()
    
    if not selected:
        sys.exit(0)
    
    issue_number = int(selected.split(" - ")[0].replace("#", ""))
    issue = next((i for i in issues if i.number == issue_number), None)
    
    if not issue:
        console.print("[red]Issue not found.[/]")
        sys.exit(1)
    
    console.print(f"\n[bold]Closing Issue #{issue.number}:[/] {issue.title}")
    console.print(f"[dim]URL: {issue.html_url}[/]\n")
    
    # 3. Add closing comment (optional)
    add_comment = questionary.confirm("Add a closing comment?", default=False).ask()
    comment = None
    
    if add_comment:
        comment = questionary.text("Closing comment:").ask()
    
    # 4. Confirm close
    console.print(f"\n[bold]Close Summary:[/]")
    console.print(f"  Issue: #{issue.number} - {issue.title}")
    if comment:
        console.print(f"  Comment: {comment}")
    
    if not questionary.confirm("Proceed with closing?").ask():
        console.print("[yellow]Close cancelled.[/]")
        sys.exit(0)
    
    # 5. Close Issue
    try:
        with console.status("Closing issue..."):
            if comment:
                issue.create_comment(comment)
            issue.edit(state='closed')
        
        console.print(f"[bold green]✓ Issue #{issue.number} closed successfully![/]")
        
        # 6. Update Project Status (if configured)
        proj_conf = config.get('projects_v2', {})
        if proj_conf.get('enabled'):
            console.print("[dim]Note: Project status should be updated to 'Done' manually or via automation.[/]")
            # Full implementation would require GraphQL to update project item field
            
    except Exception as e:
        console.print(f"[red]Failed to close issue: {e}[/]")
        sys.exit(1)

if __name__ == "__main__":
    main()
