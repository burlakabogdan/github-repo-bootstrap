
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add scripts directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts')))

from create_issue import add_issue_to_project

# Patch where the functions are defined, not where they are imported (since they are imported inside the function)
@patch("bootstrap.ensure_project_v2")
@patch("project_utils.add_item_to_project")
@patch("project_utils.set_project_item_status")
@patch("create_issue.console")
def test_add_issue_to_project_success(mock_console, mock_set_status, mock_add_item, mock_ensure_project):
    # Mock successful project retrieval (EXISTS)
    mock_ensure_project.return_value = {
        "type": "EXISTS",
        "id": "proj123"
    }
    
    # Mock adding item
    mock_add_item.return_value = "item456"
    
    # Execute
    add_issue_to_project("issueNode789", "userLogin", "MyProject")
    
    # Verify
    mock_ensure_project.assert_called_with("userLogin", "MyProject")
    mock_add_item.assert_called_with("proj123", "issueNode789")
    mock_set_status.assert_called_with("proj123", "item456", "Backlog")
    mock_console.print.assert_called_with("[green]Added Issue to Project 'MyProject'[/]")

@patch("bootstrap.ensure_project_v2")
def test_add_issue_to_project_create_success(mock_ensure_project):
    # Mock CREATE action
    mock_create_action = MagicMock(return_value={"id": "newProj123"})
    
    mock_ensure_project.return_value = {
        "type": "CREATE",
        "action": mock_create_action
    }
    
    with patch("project_utils.add_item_to_project") as mock_add, \
         patch("project_utils.set_project_item_status") as mock_set:
        
        mock_add.return_value = "item1"
        
        add_issue_to_project("node1", "user", "proj")
        
        mock_create_action.assert_called_once()
        mock_add.assert_called_with("newProj123", "node1")

@patch("bootstrap.ensure_project_v2")
def test_add_issue_to_project_failure(mock_ensure_project):
    with patch("create_issue.console") as mock_console:
        mock_ensure_project.side_effect = Exception("API Error")
        
        add_issue_to_project("node1", "user", "proj")
        
        mock_console.print.assert_called_with("[red]Failed to add to project: API Error[/]")
