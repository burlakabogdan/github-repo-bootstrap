
import json
import subprocess
from rich.console import Console

console = Console()

def gql_request(query, variables=None):
    """Execute GraphQL query using gh CLI."""
    input_data = {'query': query, 'variables': variables or {}}
    input_json = json.dumps(input_data)
    
    try:
        # gh api graphql --input -
        res = subprocess.run(
            ["gh", "api", "graphql", "--input", "-"],
            input=input_json,
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(res.stdout)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]GraphQL Request Failed: {e.stderr}[/]")
        raise
    except json.JSONDecodeError as e:
        console.print(f"[red]Failed to decode GraphQL response: {e}[/]")
        raise

def get_project_fields(project_id):
    """Get all fields for a project."""
    query = """
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          fields(first: 20) {
            nodes {
              ... on ProjectV2Field {
                id
                name
              }
              ... on ProjectV2SingleSelectField {
                id
                name
                options {
                  id
                  name
                }
              }
              ... on ProjectV2IterationField {
                id
                name
                configuration {
                  iterations {
                    id
                    title
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    res = gql_request(query, {"projectId": project_id})
    return res['data']['node']['fields']['nodes']

def set_project_item_status(project_id, item_id, status_name):
    """Set the status of a project item."""
    try:
        fields = get_project_fields(project_id)
        status_field = next((f for f in fields if f['name'] == "Status"), None)
        
        if not status_field:
            console.print("[yellow]Status field not found in project.[/]")
            return False
            
        # Find option ID for the status name (case-insensitive)
        option = next((opt for opt in status_field.get('options', []) 
                      if opt['name'].lower() == status_name.lower()), None)
                      
        if not option:
            console.print(f"[yellow]Status '{status_name}' not found in project options.[/]")
            return False
            
        mutation = """
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
          updateProjectV2ItemFieldValue(
            input: {
              projectId: $projectId
              itemId: $itemId
              fieldId: $fieldId
              value: {
                singleSelectOptionId: $optionId
              }
            }
          ) {
            projectV2Item {
              id
            }
          }
        }
        """
        
        gql_request(mutation, {
            "projectId": project_id,
            "itemId": item_id,
            "fieldId": status_field['id'],
            "optionId": option['id']
        })
        console.print(f"[green]Set item status to '{status_name}'[/]")
        return True
        
    except Exception as e:
        console.print(f"[red]Failed to set status: {e}[/]")
        return False

def find_project_item_by_content(project_id, content_id):
    """Find a project item ID by its content (issue/PR) node ID."""
    # Note: ProjectV2 doesn't have a direct lookup by content ID in the same way.
    # We have to fetch items and filter, which is inefficient but standard for V2 API currently.
    # Or we can use the node(id: contentId) { projectItems } query which is better!
    
    query = """
    query($contentId: ID!) {
      node(id: $contentId) {
        ... on Issue {
          projectItems(first: 10, includeArchived: false) {
            nodes {
              id
              project {
                id
              }
            }
          }
        }
        ... on PullRequest {
          projectItems(first: 10, includeArchived: false) {
            nodes {
              id
              project {
                id
              }
            }
          }
        }
      }
    }
    """
    res = gql_request(query, {"contentId": content_id})
    
    if not res.get('data') or not res['data'].get('node'):
        return None
        
    items = res['data']['node'].get('projectItems', {}).get('nodes', [])
    
    # Find item belonging to our project
    target_item = next((item for item in items if item['project']['id'] == project_id), None)
    
    return target_item['id'] if target_item else None

def add_item_to_project(project_id, content_id):
    """Add an item (Issue/PR) to the project and return the item ID."""
    query = """
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
        item { id }
      }
    }
    """
    res = gql_request(query, {"projectId": project_id, "contentId": content_id})
    return res['data']['addProjectV2ItemById']['item']['id']
