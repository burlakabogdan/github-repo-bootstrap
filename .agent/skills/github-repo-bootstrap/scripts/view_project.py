
import sys
from collections import defaultdict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from utils import load_config, get_github_client, get_current_repo

console = Console()
config = load_config()

def main():
    console.print("[bold blue]View Project Board[/]")
    
    try:
        g = get_github_client()
        repo = get_current_repo(g)
    except Exception as e:
        console.print(f"[red]Failed to initialize GitHub client: {e}[/]")
        sys.exit(1)
    
    console.print("[yellow]Note: This displays issues/PRs grouped by status labels.[/]")
    console.print("[yellow]For full Projects v2 view, use GitHub web UI or gh CLI.[/]\n")
    
    # Fetch all open issues and PRs
    try:
        issues_list = list(repo.get_issues(state='open'))
        issues = [i for i in issues_list if not i.pull_request]
        prs = list(repo.get_pulls(state='open'))
    except Exception as e:
        console.print(f"[red]Failed to fetch items: {e}[/]")
        sys.exit(1)
    
    # Group by status labels
    status_groups = defaultdict(list)
    status_order = ["backlog", "ready", "in-progress", "review", "done"]
    
    # Process issues
    for issue in issues:
        status = "backlog"  # default
        for label in issue.labels:
            if label.name.startswith("status:"):
                status = label.name.replace("status:", "")
                break
        status_groups[status].append(("Issue", issue))
    
    # Process PRs (default to review)
    for pr in prs:
        status = "review"  # default for PRs
        # Could check labels if PRs also have status labels
        status_groups[status].append(("PR", pr))
    
    # Display board
    console.print(Panel.fit("[bold]Project Board[/]", border_style="blue"))
    
    for status in status_order:
        items = status_groups.get(status, [])
        
        if not items and status not in ["backlog", "in-progress", "review"]:
            continue  # Skip empty non-essential columns
        
        # Create table for this status
        table = Table(title=f"{status.upper().replace('-', ' ')} ({len(items)})", 
                     show_header=True, header_style="bold")
        table.add_column("Type", style="cyan", width=6)
        table.add_column("#", style="yellow", width=6)
        table.add_column("Title", style="green")
        
        for item_type, item in items:
            table.add_row(
                item_type,
                str(item.number),
                item.title[:50] + "..." if len(item.title) > 50 else item.title
            )
        
        console.print(table)
        console.print()
    
    # Summary
    total_items = sum(len(items) for items in status_groups.values())
    console.print(f"[dim]Total items: {total_items}[/]")

if __name__ == "__main__":
    main()
