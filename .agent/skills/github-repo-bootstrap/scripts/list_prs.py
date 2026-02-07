
import sys
import questionary
from rich.console import Console
from rich.table import Table
from utils import load_config, get_github_client, get_current_repo

console = Console()
config = load_config()

def main():
    console.print("[bold blue]List Pull Requests[/]")
    
    try:
        g = get_github_client()
        repo = get_current_repo(g)
    except Exception as e:
        console.print(f"[red]Failed to initialize GitHub client: {e}[/]")
        sys.exit(1)
    
    # 1. Filter options
    state = questionary.select(
        "PR state:",
        choices=["open", "closed", "all"],
        default="open"
    ).ask()
    
    if not state:
        sys.exit(0)
    
    # 2. Fetch PRs
    try:
        prs = list(repo.get_pulls(state=state))
    except Exception as e:
        console.print(f"[red]Failed to fetch PRs: {e}[/]")
        sys.exit(1)
    
    if not prs:
        console.print(f"[yellow]No {state} PRs found.[/]")
        sys.exit(0)
    
    # 3. Display PRs
    table = Table(title=f"{state.capitalize()} Pull Requests ({len(prs)})")
    table.add_column("#", style="cyan", width=6)
    table.add_column("Title", style="green")
    table.add_column("Author", style="magenta", width=12)
    table.add_column("Branch", style="yellow", width=20)
    table.add_column("Reviews", style="blue", width=12)
    table.add_column("State", style="white", width=10)
    
    for pr in prs:
        # Get review status
        try:
            reviews = list(pr.get_reviews())
            approved = any(r.state == "APPROVED" for r in reviews)
            changes_req = any(r.state == "CHANGES_REQUESTED" for r in reviews)
            
            if approved:
                review_status = "✓ Approved"
            elif changes_req:
                review_status = "✗ Changes"
            else:
                review_status = "⏳ Pending"
        except:
            review_status = "-"
        
        # State with icon
        if pr.merged:
            state_display = "🟣 Merged"
        elif pr.state == "open":
            state_display = "🟢 Open"
        else:
            state_display = "🔴 Closed"
        
        table.add_row(
            str(pr.number),
            pr.title[:40] + "..." if len(pr.title) > 40 else pr.title,
            pr.user.login,
            f"{pr.head.ref[:18]}..." if len(pr.head.ref) > 18 else pr.head.ref,
            review_status,
            state_display
        )
    
    console.print(table)
    console.print(f"\n[dim]Total: {len(prs)} PR(s)[/]")

if __name__ == "__main__":
    main()
