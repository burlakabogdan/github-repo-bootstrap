
import sys
import questionary
from rich.console import Console
from rich.table import Table
from utils import load_config, get_github_client, get_current_repo

console = Console()
config = load_config()

def main():
    console.print("[bold blue]List Issues[/]")
    
    try:
        g = get_github_client()
        repo = get_current_repo(g)
    except Exception as e:
        console.print(f"[red]Failed to initialize GitHub client: {e}[/]")
        sys.exit(1)
    
    # 1. Filter options
    state = questionary.select(
        "Issue state:",
        choices=["open", "closed", "all"],
        default="open"
    ).ask()
    
    if not state:
        sys.exit(0)
    
    # 2. Label filter (optional)
    filter_by_label = questionary.confirm("Filter by label?", default=False).ask()
    label_filter = None
    
    if filter_by_label:
        try:
            labels = [l.name for l in repo.get_labels()]
            if labels:
                label_filter = questionary.select("Select label:", choices=labels).ask()
        except Exception as e:
            console.print(f"[yellow]Could not fetch labels: {e}[/]")
    
    # 3. Fetch issues
    try:
        if label_filter:
            issues_list = list(repo.get_issues(state=state, labels=[label_filter]))
        else:
            issues_list = list(repo.get_issues(state=state))
        
        # Filter out pull requests
        issues = [i for i in issues_list if not i.pull_request]
    except Exception as e:
        console.print(f"[red]Failed to fetch issues: {e}[/]")
        sys.exit(1)
    
    if not issues:
        console.print(f"[yellow]No {state} issues found.[/]")
        sys.exit(0)
    
    # 4. Display issues
    table = Table(title=f"{state.capitalize()} Issues ({len(issues)})")
    table.add_column("#", style="cyan", width=6)
    table.add_column("Title", style="green")
    table.add_column("Labels", style="magenta", width=20)
    table.add_column("Assignee", style="yellow", width=12)
    table.add_column("State", style="blue", width=8)
    
    for issue in issues:
        labels = ", ".join([l.name for l in issue.labels[:3]]) if issue.labels else "-"
        if len(issue.labels) > 3:
            labels += "..."
        
        assignee = issue.assignee.login if issue.assignee else "-"
        state_icon = "🟢" if issue.state == "open" else "🔴"
        
        table.add_row(
            str(issue.number),
            issue.title[:50] + "..." if len(issue.title) > 50 else issue.title,
            labels,
            assignee,
            f"{state_icon} {issue.state}"
        )
    
    console.print(table)
    console.print(f"\n[dim]Total: {len(issues)} issue(s)[/]")

if __name__ == "__main__":
    main()
