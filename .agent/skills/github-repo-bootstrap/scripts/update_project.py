
import sys
import questionary
from rich.console import Console
from rich.table import Table
from utils import load_config, get_github_client, get_current_repo

console = Console()
config = load_config()

def main():
    console.print("[bold blue]Update Project Status[/]")
    
    console.print("[yellow]Note: This is a simplified version.[/]")
    console.print("[yellow]Full GraphQL implementation for Projects v2 field updates is complex.[/]")
    console.print("[yellow]For now, use GitHub web UI or gh CLI for project updates.[/]\n")
    
    try:
        g = get_github_client()
        repo = get_current_repo(g)
    except Exception as e:
        console.print(f"[red]Failed to initialize GitHub client: {e}[/]")
        sys.exit(1)
    
    # 1. Choose item type
    item_type = questionary.select(
        "What to update?",
        choices=["Issue", "Pull Request"]
    ).ask()
    
    if not item_type:
        sys.exit(0)
    
    # 2. List items
    try:
        if item_type == "Issue":
            items_list = list(repo.get_issues(state='open'))
            items = [i for i in items_list if not i.pull_request]
        else:
            items = list(repo.get_pulls(state='open'))
    except Exception as e:
        console.print(f"[red]Failed to fetch items: {e}[/]")
        sys.exit(1)
    
    if not items:
        console.print(f"[yellow]No open {item_type.lower()}s found.[/]")
        sys.exit(0)
    
    # Display items
    table = Table(title=f"Open {item_type}s")
    table.add_column("#", style="cyan")
    table.add_column("Title", style="green")
    
    for item in items:
        table.add_row(
            str(item.number),
            item.title[:60] + "..." if len(item.title) > 60 else item.title
        )
    
    console.print(table)
    
    # 3. Select item
    item_choices = [f"#{i.number} - {i.title}" for i in items]
    selected = questionary.select(f"Select {item_type.lower()}:", choices=item_choices).ask()
    
    if not selected:
        sys.exit(0)
    
    item_number = int(selected.split(" - ")[0].replace("#", ""))
    item = next((i for i in items if i.number == item_number), None)
    
    if not item:
        console.print(f"[red]{item_type} not found.[/]")
        sys.exit(1)
    
    console.print(f"\n[bold]Selected {item_type} #{item.number}:[/] {item.title}\n")
    
    # 4. Choose what to update
    update_choice = questionary.select(
        "What to update?",
        choices=[
            "Status (via labels)",
            "Priority (via labels)",
            "Assignee"
        ]
    ).ask()
    
    if not update_choice:
        sys.exit(0)
    
    # 5. Apply update
    try:
        if "Status" in update_choice:
            status_labels = ["status:backlog", "status:ready", "status:in-progress", "status:review", "status:done"]
            status = questionary.select("New status:", choices=status_labels).ask()
            
            if status:
                # Remove old status labels
                current_labels = [l.name for l in item.labels if not l.name.startswith("status:")]
                current_labels.append(status)
                item.edit(labels=current_labels)
                console.print(f"[green]✓ Status updated to '{status}'[/]")
        
        elif "Priority" in update_choice:
            priority_labels = ["p0", "p1", "p2"]
            priority = questionary.select("New priority:", choices=priority_labels).ask()
            
            if priority:
                # Remove old priority labels
                current_labels = [l.name for l in item.labels if l.name not in ["p0", "p1", "p2"]]
                current_labels.append(priority)
                item.edit(labels=current_labels)
                console.print(f"[green]✓ Priority updated to '{priority}'[/]")
        
        elif "Assignee" in update_choice:
            assignee = questionary.text("Assignee username (leave empty to unassign):").ask()
            
            if assignee:
                item.add_to_assignees(assignee)
                console.print(f"[green]✓ Assigned to '{assignee}'[/]")
            else:
                if item.assignee:
                    item.remove_from_assignees(item.assignee)
                    console.print(f"[green]✓ Unassigned[/]")
    
    except Exception as e:
        console.print(f"[red]Failed to update: {e}[/]")
        sys.exit(1)

if __name__ == "__main__":
    main()
