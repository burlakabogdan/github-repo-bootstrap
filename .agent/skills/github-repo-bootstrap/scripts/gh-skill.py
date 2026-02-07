#!/usr/bin/env python3
"""
GitHub Repo Bootstrap Skill - Main CLI Entry Point
Unified interface for all GitHub workflow commands.
"""

import sys
import questionary
from rich.console import Console

console = Console()

__version__ = "1.0.0"

COMMANDS = {
    "version": {
        "desc": "Show version",
        "script": None
    },
    "bootstrap": {
        "desc": "Bootstrap repository with labels, templates, and project",
        "script": "bootstrap.py"
    },
    "create-issue": {
        "desc": "Create a new issue",
        "script": "create_issue.py"
    },
    "create-branch": {
        "desc": "Create a branch from an issue",
        "script": "create_branch.py"
    },
    "commit": {
        "desc": "Commit changes with conventional format",
        "script": "commit_check.py"
    },
    "create-pr": {
        "desc": "Create a pull request",
        "script": "create_pr.py"
    },
    "review-pr": {
        "desc": "Review a pull request",
        "script": "review_pr.py"
    },
    "merge-pr": {
        "desc": "Merge a pull request",
        "script": "merge_pr.py"
    },
    "close-issue": {
        "desc": "Close an issue",
        "script": "close_issue.py"
    },
    "list-issues": {
        "desc": "List issues",
        "script": "list_issues.py"
    },
    "list-prs": {
        "desc": "List pull requests",
        "script": "list_prs.py"
    },
    "view-project": {
        "desc": "View project board",
        "script": "view_project.py"
    },
    "update-project": {
        "desc": "Update project item status/priority",
        "script": "update_project.py"
    },
    "install-hooks": {
        "desc": "Install Git hooks",
        "script": "install_hooks.py"
    }
}

def show_menu():
    """Show interactive menu to select command."""
    console.print("\n[bold blue]GitHub Repo Bootstrap Skill[/]")
    console.print("Select a command:\n")
    
    choices = [
        questionary.Choice(
            title=f"{cmd}: {info['desc']}",
            value=cmd
        )
        for cmd, info in COMMANDS.items()
    ]
    
    selected = questionary.select(
        "Command:",
        choices=choices
    ).ask()
    
    if not selected:
        console.print("Cancelled.")
        sys.exit(0)
    
    return selected

def run_command(command):
    """Run the selected command by importing and executing its main function."""
    if command == "version":
        console.print(f"GitHub Repo Bootstrap Skill v{__version__}")
        return

    script_name = COMMANDS[command]["script"]
    module_name = script_name.replace(".py", "")
    
    try:
        # Import the module dynamically
        module = __import__(module_name)
        
        # Run the main function
        if hasattr(module, 'main'):
            module.main()
        else:
            console.print(f"[red]Error: {script_name} does not have a main() function[/]")
            sys.exit(1)
            
    except ImportError as e:
        console.print(f"[red]Error importing {script_name}: {e}[/]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error running {command}: {e}[/]")
        sys.exit(1)

def main():
    """Main entry point."""
    # If command provided as argument, run it directly
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command in COMMANDS:
            run_command(command)
        elif command in ["-h", "--help", "help"]:
            console.print("\n[bold]GitHub Repo Bootstrap Skill[/]\n")
            console.print("Usage: python gh-skill.py [command]\n")
            console.print("Available commands:")
            for cmd, info in COMMANDS.items():
                console.print(f"  [cyan]{cmd:20}[/] {info['desc']}")
            console.print("\nRun without arguments for interactive menu.")
        else:
            console.print(f"[red]Unknown command: {command}[/]")
            console.print("Run 'python gh-skill.py help' for available commands.")
            sys.exit(1)
    else:
        # Show interactive menu
        command = show_menu()
        run_command(command)

if __name__ == "__main__":
    main()
