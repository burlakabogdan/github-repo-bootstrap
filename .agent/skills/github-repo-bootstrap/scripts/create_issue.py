
import sys
import questionary
from rich.console import Console
from utils import load_config, get_github_client, get_current_repo

console = Console()
config = load_config()

def add_issue_to_project(issue_node_id, user_login, project_title):
    # This requires GraphQL. We can reuse bootstrap logic or duplicate simple query.
    # For MVP, let's try to reuse bootstrap's ensure_project (to get ID) and then add item?
    # Or just simpler:
    from bootstrap import ensure_project_v2, gql_request
    
    try:
        proj_action = ensure_project_v2(user_login, project_title)
        project_id = proj_action['id'] 
        if not project_id and proj_action['type'] == 'CREATE': 
             # It means we didn't execute the create action here. 
             # We should probably assume project exists if bootstrap ran.
             # If not, we might fail or need to create it.
             # Let's run the action if it's CREATE? No, that might be too much side effect.
             # For now, just warn.
             console.print("[yellow]Project not found or not created. Skipping link.[/]")
             return
             
        # Add Item Mutation
        q_add = """
        mutation($projectId: ID!, $contentId: ID!) {
          addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
            item { id }
          }
        }
        """
        gql_request(q_add, {"projectId": project_id, "contentId": issue_node_id})
        console.print(f"[green]Added Issue to Project '{project_title}'[/]")
        
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
                add_issue_to_project(issue.raw_data['node_id'], user.login, proj_conf.get('title', 'Work'))
    else:
        console.print("Cancelled.")

if __name__ == "__main__":
    main()
