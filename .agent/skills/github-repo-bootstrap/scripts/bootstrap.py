
import sys
import os
import subprocess
import requests
import json
import questionary
from rich.console import Console
from rich.table import Table
from rich.progress import track

from utils import load_config, get_github_client, get_current_repo, RepositoryNotFoundError

console = Console()
config = load_config()

def sync_labels(repo, intended_labels):
    """Create or update labels."""
    existing = {l.name: l for l in repo.get_labels()}
    
    actions = []
    
    for name, color_desc in intended_labels.items():
        # In config, we have list of strings "type:bug", or dict? 
        # Config structure in yaml is: labels: type: ["type:bug", ...]
        # Let's simplify: flattened list of objects needed.
        pass

    # Re-reading config structure:
    # labels:
    #   type: ["type:bug", ...]
    #   priority: ["p0", ...]
    
    # We'll map them to colors for now (defaults)
    COLORS = {
        "type:bug": "d73a4a",
        "type:feature": "a2eeef",
        "type:refactor": "cfd3d7",
        "type:docs": "0075ca",
        "p0": "b60205",
        "p1": "ff9f1c",
        "p2": "f9c74f"
    }
    
    flattened = []
    for cat, items in intended_labels.items():
        for item in items:
            flattened.append((item, COLORS.get(item, "ededed")))
            
    for name, color in flattened:
        if name not in existing:
            action = lambda n=name, c=color: repo.create_label(name=n, color=c)
            actions.append({"name": name, "type": "CREATE", "action": action})
        else:
            # Check color match? Optional. For now just create missing.
            pass
            
    return actions

def gql_request(query, variables=None):
    # Use gh api to avoid requests/token issues
    import subprocess
    import json
    
    input_data = {'query': query, 'variables': variables or {}}
    input_json = json.dumps(input_data)
    
    try:
        # gh api graphql --input -
        # We need to ensure we run it in a way that captures output
        res = subprocess.run(
            ["gh", "api", "graphql", "--input", "-"],
            input=input_json,
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(res.stdout)
        
        if 'errors' in data:
            raise Exception(f"GraphQL Error: {json.dumps(data['errors'], indent=2)}")
        if 'data' not in data:
             raise Exception(f"GraphQL Response missing data: {json.dumps(data, indent=2)}")
        return data
        
    except subprocess.CalledProcessError as e:
        raise Exception(f"Query failed: {e.stderr}")
    except Exception as e:
        raise Exception(f"GraphQL invocation failed: {e}")

def ensure_project_v2(user_login, project_title):
    # 1. Find user node ID
    # 1. Find user node ID
    q_user = """
    query($login: String!, $title: String!) {
      user(login: $login) {
        id
        projectsV2(first: 20, query: $title) {
          nodes { id title url closed }
        }
      }
    }
    """
    res = gql_request(q_user, {"login": user_login, "title": project_title})
    user_id = res['data']['user']['id']
    existing = res['data']['user']['projectsV2']['nodes']
    
    target = next((p for p in existing if p['title'] == project_title), None)
    
    if target:
        return {"name": project_title, "type": "EXISTS", "id": target['id'], "url": target['url'], "closed": target['closed'], "action": lambda: target['url']}
    else:
        # Create action
        def create():
            q_create = """
            mutation($ownerId: ID!, $title: String!) {
              createProjectV2(input: {ownerId: $ownerId, title: $title}) {
                projectV2 { id url }
              }
            }
            """
            r = gql_request(q_create, {"ownerId": user_id, "title": project_title})
            return r['data']['createProjectV2']['projectV2']['url']
            
        return {"name": project_title, "type": "CREATE", "action": create}

def get_repo_id(owner, name):
    q = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        id
      }
    }
    """
    res = gql_request(q, {"owner": owner, "name": name})
    return res['data']['repository']['id']

def link_project_to_repo(project_id, repo_id):
    q = """
    mutation($projectId: ID!, $repositoryId: ID!) {
      linkProjectV2ToRepository(input: {projectId: $projectId, repositoryId: $repositoryId}) {
        repository { id }
      }
    }
    """
    try:
        gql_request(q, {"projectId": project_id, "repositoryId": repo_id})
        return True
    except Exception as e:
        if "already linked" in str(e).lower():
            return False
        # Ignore other errors for now? Or warn?
        console.print(f"[yellow]Warning: Failed to link project: {e}[/]")
        return False

def get_project_fields(project_id):
    q = """
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          fields(first: 20) {
            nodes {
              ... on ProjectV2Field { id name dataType }
              ... on ProjectV2SingleSelectField { id name dataType options { id name } }
            }
          }
        }
      }
    }
    """
    res = gql_request(q, {"projectId": project_id})
    return res['data']['node']['fields']['nodes']

def create_single_select_field(project_id, name, options):
    # options is list of strings
    formatted_options = [{"name": opt, "color": "GRAY", "description": ""} for opt in options]
    
    q = """
    mutation($projectId: ID!, $name: String!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
      createProjectV2Field(input: {
        projectId: $projectId, 
        dataType: SINGLE_SELECT, 
        name: $name, 
        singleSelectOptions: $options
      }) {
        projectV2Field {
          ... on ProjectV2SingleSelectField {
             id 
             name
          }
        }
      }
    }
    """
    try:
        gql_request(q, {"projectId": project_id, "name": name, "options": formatted_options})
        return True
    except Exception as e:
        console.print(f"[red]Failed to create field {name}: {e}[/]")
        return False

def update_single_select_field(field_node, desired_options):
    # field_node comes from get_project_fields result
    current_options = field_node.get('options', [])
    current_map = {opt['name']: opt['id'] for opt in current_options}
    
    final_options_input = []
    
    # 1. Add desired options (preserving order)
    for name in desired_options:
        opt_input = {"name": name, "color": "GRAY", "description": ""}
        # ID is not accepted in input? Matching by name?
        # If ID is invalid, we omit it.
        final_options_input.append(opt_input)
        
    # 2. Append existing options not in desired (to avoid deletion errors)
    for name, oid in current_map.items():
        if name not in desired_options:
             final_options_input.append({"name": name, "color": "GRAY", "description": ""}) 
 
    q = """
    mutation($fieldId: ID!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
      updateProjectV2Field(input: {
        fieldId: $fieldId, 
        singleSelectOptions: $options
      }) {
        projectV2Field {
          ... on ProjectV2SingleSelectField {
             id 
             name
          }
        }
      }
    }
    """
    try:
        gql_request(q, {"fieldId": field_node['id'], "options": final_options_input})
        return True
    except Exception as e:
        console.print(f"[red]Failed to update field {field_node['name']}: {e}[/]")
        return False

def main():
    console.print("[bold blue]GitHub Repo Bootstrap[/]")
    
    try:
        g = get_github_client()
        try:
            repo = get_current_repo(g, raise_error=True)
        except RepositoryNotFoundError:
            console.print("[yellow]No existing repository detected.[/]")
            if not questionary.confirm("Initialize and create a new GitHub repository here?").ask():
                console.print("Exiting.")
                sys.exit(0)
                
            # Create interactive flow
            repo_name = questionary.text("Repository Name:", default=os.path.basename(os.getcwd())).ask()
            visibility = questionary.select("Visibility:", choices=["public", "private", "internal"]).ask()
            
            with console.status(f"Creating repository {repo_name}..."):
                # Initialize git if not already
                if not os.path.exists(".git"):
                    subprocess.check_call(["git", "init"])

                # gh repo create <name> --<vis> --source=. --remote=origin
                cmd = ["gh", "repo", "create", repo_name, f"--{visibility}", "--source=.", "--remote=origin"]
                subprocess.check_call(cmd)
                
            console.print(f"[green]Successfully created repository {repo_name}![/]")
            # Re-fetch repo
            repo = get_current_repo(g)
        user = g.get_user()
        
        console.print(f"Repository: [green]{repo.full_name}[/]")
        console.print(f"User: [green]{user.login}[/]")
        
        # 1. Plan Labels
        label_actions = sync_labels(repo, config.get('labels', {}))

        # 2. Plan Templates
        from pathlib import Path
        template_actions = []
        script_dir = Path(__file__).parent
        assets_dir = script_dir.parent / "assets" / "templates"
        
        if assets_dir.exists():
            for template_file in assets_dir.glob("*.md"):
                dest_path = f".github/ISSUE_TEMPLATE/{template_file.name}"
                if "PULL_REQUEST" in template_file.name:
                    dest_path = ".github/PULL_REQUEST_TEMPLATE.md"
                    
                def upload_action(tf=template_file, dp=dest_path):
                    with open(tf, "r", encoding="utf-8") as f: content = f.read()
                    try:
                        contents = repo.get_contents(dp)
                        repo.update_file(contents.path, f"Update {dp}", content, contents.sha)
                        console.print(f"Updated {dp}")
                    except:
                        repo.create_file(dp, f"Create {dp}", content)
                        console.print(f"Created {dp}")

                template_actions.append({"name": dest_path, "type": "UPLOAD", "action": upload_action})

        # 3. Plan Project
        proj_config = config.get('projects_v2', {})
        proj_action = None
        if proj_config.get('enabled'):
            try:
                proj_action = ensure_project_v2(user.login, proj_config.get('title', 'Work'))
            except Exception as e:
                console.print(f"[red]Failed to query Projects v2: {e}[/]")
                # If project config is enabled, this should be a blocker or at least clearly failed
                console.print("[red]Aborting bootstrap due to Project v2 error. Please check token scopes (need 'project').[/]")
                sys.exit(1)
        
        # Display Plan
        table = Table(title="Bootstrap Plan")
        table.add_column("Category")
        table.add_column("Item")
        table.add_column("Action", style="bold")
        
        for a in label_actions:
            table.add_row("Label", a['name'], f"[green]{a['type']}[/]")
            
        for a in template_actions:
             table.add_row("File", a['name'], f"[green]{a['type']}[/]")
            
        if proj_action:
            style = "green" if proj_action['type'] == "CREATE" else "dim"
            table.add_row("Project", proj_action['name'], f"[{style}]{proj_action['type']}[/]")
        
        if not label_actions and not template_actions and (not proj_action or proj_action['type'] == "EXISTS"):
            console.print("[green]Nothing to do! Repository is already compliant.[/]")
            return

        console.print(table)
        
        # Confirm
        ans = questionary.select(
            "Execute these changes?",
            choices=["Run", "Dry-run", "Cancel"]
        ).ask()
        
        if ans == "Cancel":
            console.print("Aborted.")
            sys.exit(0)
            
        if ans == "Run":
            project_url = None
            with console.status("Applying changes..."):
                # Labels
                for a in label_actions:
                    a['action']()
                    console.print(f"Created label {a['name']}")
                
                # Templates
                for a in template_actions:
                    a['action']()
                
                # Project
                if proj_action:
                    project_url = proj_action['action']()
                    
            console.print("[bold green]Success![/]")
            
            if project_url:
                console.print(f"Project v2 URL: [link={project_url}]{project_url}[/link]")
                if proj_action.get('active') is False or proj_action.get('closed') is True:
                     console.print("[yellow]Note: This project appears to be closed.[/]")
                     
                # Link and Configure (Moved out of status block for visibility)
                if proj_action:
                     try:
                        owner, name = repo.full_name.split('/')
                        repo_node_id = get_repo_id(owner, name)
                        if link_project_to_repo(proj_action['id'], repo_node_id):
                            console.print(f"Linked project to {repo.full_name}")
                        
                        # Configure Fields
                        console.print("Configuring project fields...")
                        fields = get_project_fields(proj_action['id'])
                        
                        # Status
                        status_field = next((f for f in fields if f['name'] == "Status"), None)
                        desired_status = proj_config.get('fields', {}).get('status', [])
                        if status_field and desired_status:
                                update_single_select_field(status_field, desired_status)
                                console.print("Updated Status options")
                        
                        # Priority
                        priority_field = next((f for f in fields if f['name'] == "Priority"), None)
                        desired_priority = proj_config.get('fields', {}).get('priority', [])
                        if not priority_field and desired_priority:
                            if create_single_select_field(proj_action['id'], "Priority", desired_priority):
                                console.print("Created Priority field")
                        elif priority_field and desired_priority:
                                update_single_select_field(priority_field, desired_priority)
                                console.print("Updated Priority options")

                     except Exception as e:
                        console.print(f"[red]Failed to link/configure project: {e}[/]")
            
    except Exception as e:
        console.print(f"[red]Critical Error: {e}[/]")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
