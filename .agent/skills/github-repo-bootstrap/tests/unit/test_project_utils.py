
import pytest
from unittest.mock import patch, MagicMock
import json
import subprocess
import sys
import os

# Add scripts directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts')))

from project_utils import gql_request, get_project_fields, set_project_item_status, add_item_to_project, find_project_item_by_content

# --- Fixtures ---

@pytest.fixture
def mock_subprocess():
    with patch("subprocess.run") as mock:
        yield mock

@pytest.fixture
def mock_console():
    with patch("project_utils.console") as mock:
        yield mock

# --- Tests for gql_request ---

def test_gql_request_success(mock_subprocess):
    mock_subprocess.return_value.stdout = '{"data": {"key": "value"}}'
    result = gql_request("query { ... }")
    assert result == {"data": {"key": "value"}}
    mock_subprocess.assert_called_once()

def test_gql_request_failure(mock_subprocess, mock_console):
    mock_subprocess.side_effect = subprocess.CalledProcessError(1, ["gh"], stderr="Error message")
    with pytest.raises(subprocess.CalledProcessError):
        gql_request("query { ... }")
    mock_console.print.assert_called_with("[red]GraphQL Request Failed: Error message[/]")

def test_gql_request_json_error(mock_subprocess, mock_console):
    mock_subprocess.return_value.stdout = "Invalid JSON"
    with pytest.raises(json.JSONDecodeError):
        gql_request("query { ... }")
    mock_console.print.assert_called()

# --- Tests for get_project_fields ---

@patch("project_utils.gql_request")
def test_get_project_fields(mock_gql):
    mock_response = {
        "data": {
            "node": {
                "fields": {
                    "nodes": [
                        {"id": "field1", "name": "Status"},
                        {"id": "field2", "name": "Priority"}
                    ]
                }
            }
        }
    }
    mock_gql.return_value = mock_response
    fields = get_project_fields("proj123")
    assert len(fields) == 2
    assert fields[0]["name"] == "Status"

# --- Tests for set_project_item_status ---

@patch("project_utils.gql_request")
@patch("project_utils.get_project_fields")
def test_set_project_item_status_success(mock_get_fields, mock_gql, mock_console):
    mock_get_fields.return_value = [
        {
            "id": "status_field_id",
            "name": "Status",
            "options": [
                {"id": "opt1", "name": "Backlog"},
                {"id": "opt2", "name": "Done"}
            ]
        }
    ]
    
    result = set_project_item_status("proj123", "item456", "Backlog")
    
    assert result is True
    mock_gql.assert_called_once()
    args, _ = mock_gql.call_args
    assert "updateProjectV2ItemFieldValue" in args[0]
    assert args[1]["optionId"] == "opt1"
    mock_console.print.assert_called_with("[green]Set item status to 'Backlog'[/]")

@patch("project_utils.get_project_fields")
def test_set_project_item_status_no_field(mock_get_fields, mock_console):
    mock_get_fields.return_value = [{"name": "OnlyPriority"}]
    result = set_project_item_status("proj123", "item456", "Backlog")
    assert result is False
    mock_console.print.assert_called_with("[yellow]Status field not found in project.[/]")

@patch("project_utils.get_project_fields")
def test_set_project_item_status_no_option(mock_get_fields, mock_console):
    mock_get_fields.return_value = [
        {
            "id": "status_field_id",
            "name": "Status",
            "options": [{"id": "opt1", "name": "Backlog"}]
        }
    ]
    result = set_project_item_status("proj123", "item456", "InvalidStatus")
    assert result is False
    mock_console.print.assert_called_with("[yellow]Status 'InvalidStatus' not found in project options.[/]")

# --- Tests for add_item_to_project ---

@patch("project_utils.gql_request")
def test_add_item_to_project(mock_gql):
    mock_gql.return_value = {
        "data": {
            "addProjectV2ItemById": {
                "item": {"id": "newItem123"}
            }
        }
    }
    item_id = add_item_to_project("proj123", "content456")
    assert item_id == "newItem123"
    mock_gql.assert_called_once()

# --- Tests for find_project_item_by_content ---

@patch("project_utils.gql_request")
def test_find_project_item_by_content_found(mock_gql):
    mock_gql.return_value = {
        "data": {
            "node": {
                "projectItems": {
                    "nodes": [
                        {"id": "item1", "project": {"id": "otherProj"}},
                        {"id": "targetItem", "project": {"id": "targetProj"}}
                    ]
                }
            }
        }
    }
    item_id = find_project_item_by_content("targetProj", "content123")
    assert item_id == "targetItem"

@patch("project_utils.gql_request")
def test_find_project_item_by_content_not_found(mock_gql):
    mock_gql.return_value = {
        "data": {
            "node": {
                "projectItems": {
                    "nodes": []
                }
            }
        }
    }
    item_id = find_project_item_by_content("targetProj", "content123")
    assert item_id is None
