
import sys
import questionary
from rich.console import Console
from rich.table import Table
from utils import load_config, get_github_client, get_current_repo

console = Console()
config = load_config()

def main():
    console.print("[bold blue]PR Review Assistant[/]")
    
    try:
        g = get_github_client()
        repo = get_current_repo(g)
        user = g.get_user()
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
    table.add_column("Branch", style="yellow")
    
    for pr in prs:
        table.add_row(
            str(pr.number),
            pr.title,
            pr.user.login,
            pr.head.ref
        )
    
    console.print(table)
    
    # 2. Select PR
    pr_choices = [f"#{pr.number} - {pr.title}" for pr in prs]
    selected = questionary.select("Select PR to review:", choices=pr_choices).ask()
    
    if not selected:
        sys.exit(0)
    
    pr_number = int(selected.split(" - ")[0].replace("#", ""))
    pr = next((p for p in prs if p.number == pr_number), None)
    
    if not pr:
        console.print("[red]PR not found.[/]")
        sys.exit(1)
    
    console.print(f"\n[bold]Reviewing PR #{pr.number}:[/] {pr.title}")
    console.print(f"[dim]Author: {pr.user.login} | Branch: {pr.head.ref}[/]")
    console.print(f"[dim]URL: {pr.html_url}[/]\n")
    
    # 3. Review Type
    review_types = [
        "APPROVE - Approve the changes",
        "REQUEST_CHANGES - Request changes before merging",
        "COMMENT - Add a comment without approval"
    ]
    
    review_choice = questionary.select("Review action:", choices=review_types).ask()
    
    if not review_choice:
        sys.exit(0)
    
    review_event = review_choice.split(" - ")[0]
    
    # 4. Review Comment
    comment = questionary.text(
        "Review comment (optional):",
        default="LGTM!" if review_event == "APPROVE" else ""
    ).ask()
    
    # 5. Confirm and Submit
    console.print(f"\n[bold]Review Summary:[/]")
    console.print(f"  Action: [cyan]{review_event}[/]")
    console.print(f"  Comment: {comment if comment else '[dim](none)[/]'}")
    
    if not questionary.confirm("Submit review?").ask():
        console.print("[yellow]Review cancelled.[/]")
        sys.exit(0)
    
    # 6. Submit Review
    try:
        with console.status("Submitting review..."):
            pr.create_review(
                body=comment,
                event=review_event
            )
        console.print(f"[bold green]✓ Review submitted successfully![/]")
        
        # 7. Update Project Status (if approved and configured)
        if review_event == "APPROVE":
            proj_conf = config.get('projects_v2', {})
            if proj_conf.get('enabled'):
                console.print("[dim]Updating project status...[/]")
                # Note: Setting field values requires GraphQL and field IDs
                # For MVP, we skip this complexity
                # In production, you'd call update_project_item_field here
                
    except Exception as e:
        console.print(f"[red]Failed to submit review: {e}[/]")
        sys.exit(1)

if __name__ == "__main__":
    main()
