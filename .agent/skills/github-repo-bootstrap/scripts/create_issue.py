
import sys
import questionary
from rich.console import Console
from utils import load_config, get_github_client, get_current_repo

console = Console()
config = load_config()

def add_issue_to_project(issue_node_id, user_login, project_title):
    from bootstrap import ensure_project_v2
    from project_utils import set_project_item_status, add_item_to_project
    
    try:
        proj_action = ensure_project_v2(user_login, project_title)
        
        # Handle both EXISTS and CREATE cases
        project_id = None
        if proj_action['type'] == 'EXISTS':
            project_id = proj_action['id']
        elif proj_action['type'] == 'CREATE':
            # Execute the create action to get the project
            result = proj_action['action']()
            project_id = result['id']
            
        if not project_id:
             console.print("[yellow]Project not found or not created. Skipping link.[/]")
             return
             
        # Add Item
        item_id = add_item_to_project(project_id, issue_node_id)
        console.print(f"[green]Added Issue to Project '{project_title}'[/]")
        
        # Set Status to Backlog
        set_project_item_status(project_id, item_id, "Backlog")
        
    except Exception as e:
        console.print(f"[red]Failed to add to project: {e}[/]")

def main():
    console.print("[bold blue]Create Issue[/]")
    g = get_github_client()
    repo = get_current_repo(g)
    user = g.get_user()
    
    # 1. Select Template (Mocked for now, or just Type)
    issue_type = questionary.select(
        "Issue Type:",
        choices=["Bug", "Feature", "Task", "Question"]
    ).ask()
    
    if not issue_type: sys.exit(0)
    
    # 2. Input
    title = questionary.text("Title:").ask()
    body = questionary.text("Description (Body):").ask()
    
    labels = []
    # Try to auto-label based on type
    type_map = {
        "Bug": "type:bug",
        "Feature": "type:feature",
        "Task": "type:custom", # or specific
    }
    if issue_type in type_map:
        labels.append(type_map[issue_type])
        
    # 3. Create
    if questionary.confirm(f"Create issue '{title}'?").ask():
        with console.status("Creating issue..."):
            issue = repo.create_issue(title=title, body=body, labels=labels)
            console.print(f"[bold green]Created #{issue.number}: {issue.html_url}[/]")
            
            # 4. Link to Project
            proj_conf = config.get('projects_v2', {})
            if proj_conf.get('enabled'):
                # We need Node ID for GraphQL. PyGithub Issue object has `raw_data['node_id']`?
                # Yes, issue.raw_data['node_id']
                # Use repository name if title is not specified
                project_title = proj_conf.get('title') or repo.name
                add_issue_to_project(issue.raw_data['node_id'], user.login, project_title)
    else:
        console.print("Cancelled.")

if __name__ == "__main__":
    main()
