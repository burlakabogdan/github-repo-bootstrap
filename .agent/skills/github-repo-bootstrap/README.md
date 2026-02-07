# GitHub Repo Bootstrap Skill

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.10%2B-blue)

A comprehensive toolkit to standardize GitHub repositories and streamline the development workflow. This project implements an **Antigravity Agent Skill** that provides:

1.  **Repository Bootstrap**: One-click setup of Labels, Templates, and Projects v2.
2.  **Commit Assistant**: Conventional Commits wizard with Issue linking.
3.  **Work Management**: CLI tools to create Issues, Branches, and Pull Requests.

## 📦 Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your/github-repo-bootstrap.git
    cd GitHub_Repo_Bootstrap
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r .agent/skills/github-repo-bootstrap/scripts/requirements.txt
    ```

3.  **Configuration** (Optional):
    *   The tools look for `.github/repo-skill.yml` in your target repo.
    *   Defaults are loaded from `.agent/skills/github-repo-bootstrap/assets/config.yml`.
    *   **Authentication**: Ensure `GITHUB_TOKEN` env var is set OR you are logged in via `gh auth login`.

## 🚀 Usage Examples

All scripts are located in `.agent/skills/github-repo-bootstrap/scripts/`.

### 1. Bootstrap a Repository
Sets up standard Labels (`type:bug`, `p0`...), creates `.github/ISSUE_TEMPLATE/*`, and ensures a "Work" Project v2 exists.

```bash
# Run wizard (Prompt: Run / Dry-run / Cancel)
python .agent/skills/github-repo-bootstrap/scripts/bootstrap.py
```

**Output:**
```text
GitHub Repo Bootstrap
Repository: owner/my-repo
User: owner

Bootstrap Plan:
| Category | Item                    | Action |
|----------|-------------------------|--------|
| Label    | type:bug                | EXISTS |
| Label    | type:design             | CREATE |
| File     | .github/ISSUE_TEMPLATE/ | UPLOAD |
| Project  | Work                    | CREATE |
```

## Quick Start: Unified CLI

For convenience, use the unified CLI entry point instead of calling individual scripts:

```bash
# Interactive menu - select command from list
python .agent/skills/github-repo-bootstrap/scripts/gh-skill.py

# Or run commands directly
python .agent/skills/github-repo-bootstrap/scripts/gh-skill.py bootstrap
python .agent/skills/github-repo-bootstrap/scripts/gh-skill.py create-issue
python .agent/skills/github-repo-bootstrap/scripts/gh-skill.py commit
python .agent/skills/github-repo-bootstrap/scripts/gh-skill.py create-pr

# See all available commands
python .agent/skills/github-repo-bootstrap/scripts/gh-skill.py help
```

## Individual Scripts

You can also call individual scripts directly:

### 2. Create an Issue
Interactive wizard to create an issue and automatically add it to the project.

```bash
python .agent/skills/github-repo-bootstrap/scripts/create_issue.py
```

**Workflow:**
1.  Select Type: `[Feature, Bug, Task]`
2.  Enter Title: `Add login page`
3.  Enter Body: `User should be able to...`
4.  **Result**: Creates Issue #42 and adds to "Backlog".

### 3. Start Working (Create Branch)
Pick an existing issue to invoke the branch creator.

```bash
python .agent/skills/github-repo-bootstrap/scripts/create_branch.py
```

**Workflow:**
1.  Lists open issues:
    *   `#42 Add login page`
    *   `#38 Fix css crash`
2.  Select Issue #42.
3.  Choose Type: `feat`
4.  **Result**: Creates and checks out `feat/42-add-login-page`.

### 4. Commit Changes
Pre-commit hook or CLI tool to generate Conventional Commits.

```bash
python .agent/skills/github-repo-bootstrap/scripts/commit_check.py
```

**Workflow:**
1.  **Auto-detects** Issue #42 from branch `feat/42-...`
2.  Select Type: `feat`
3.  Enter Scope (optional): `auth`
4.  Enter Subject: `implement standard login form`
5.  **Preview**: `feat(auth): implement standard login form #42`
6.  Executes `git commit`.

### 5. Create Pull Request
Push current branch and open a PR with the correct template.

```bash
python .agent/skills/github-repo-bootstrap/scripts/create_pr.py
```

**Result**:
*   Pushes `feat/42-add-login-page`.
*   Opens PR with Title "implement standard login form".
*   Body pre-filled with Template and appended with "Fixes #42".
*   Adds PR to "Work" project.

### 6. Review Pull Request
Review and approve/request changes on open PRs.

```bash
python .agent/skills/github-repo-bootstrap/scripts/review_pr.py
```

**Workflow:**
1.  Lists all open PRs with review status.
2.  Select PR to review.
3.  Choose action: `APPROVE`, `REQUEST_CHANGES`, or `COMMENT`.
4.  Add review comment.
5.  **Result**: Submits review to GitHub.

### 7. Merge Pull Request
Merge approved PRs with automatic branch cleanup.

```bash
python .agent/skills/github-repo-bootstrap/scripts/merge_pr.py
```

**Workflow:**
1.  Lists open PRs with approval and mergeable status.
2.  Select PR to merge.
3.  Choose merge method: `merge`, `squash`, or `rebase`.
4.  **Result**: Merges PR, optionally deletes branch, auto-closes linked issues.

### 8. View & Manage

**List Issues:**
```bash
python .agent/skills/github-repo-bootstrap/scripts/list_issues.py
```
Filter by state (open/closed/all) and labels.

**List PRs:**
```bash
python .agent/skills/github-repo-bootstrap/scripts/list_prs.py
```
Shows review status and merge state.

**View Project Board:**
```bash
python .agent/skills/github-repo-bootstrap/scripts/view_project.py
```
Displays issues/PRs grouped by status.

**Update Project Status:**
```bash
python .agent/skills/github-repo-bootstrap/scripts/update_project.py
```
Manually update status, priority, or assignee.

**Close Issue:**
```bash
python .agent/skills/github-repo-bootstrap/scripts/close_issue.py
```
Close issues with optional comment.

### 9. Install Pre-commit Hook
Automatically run commit checks before each commit.

```bash
python .agent/skills/github-repo-bootstrap/scripts/install_hooks.py
```

**Result**: Installs pre-commit hook that runs `commit_check.py` automatically.

## 🛠 Project Structure

```text
.agent/skills/github-repo-bootstrap/
├── assets/                  # Static resources
│   ├── config.yml           # Default configuration
│   └── templates/           # Issue/PR Markdown templates
├── scripts/                 # Executable logic
│   ├── bootstrap.py         # Repo setup logic
│   ├── commit_check.py      # Commit wizard
│   ├── create_branch.py     # Branch manager
│   ├── create_issue.py      # Issue manager
│   ├── create_pr.py         # PR manager
│   ├── review_pr.py         # PR review assistant
│   ├── merge_pr.py          # PR merge manager
│   ├── close_issue.py       # Issue closer
│   ├── update_project.py    # Project status updater
│   ├── list_issues.py       # Issue viewer
│   ├── list_prs.py          # PR viewer
│   ├── view_project.py      # Project board viewer
│   ├── install_hooks.py     # Git hooks installer
│   └── utils.py             # Shared helpers
└── SKILL.md                 # Agent Skill definition
```

## 📋 Complete Workflow Example

```bash
# 1. Bootstrap repository (one-time setup)
python .agent/skills/github-repo-bootstrap/scripts/bootstrap.py

# 2. Install pre-commit hook (optional but recommended)
python .agent/skills/github-repo-bootstrap/scripts/install_hooks.py

# 3. Create issue
python .agent/skills/github-repo-bootstrap/scripts/create_issue.py

# 4. Create branch from issue
python .agent/skills/github-repo-bootstrap/scripts/create_branch.py

# 5. Make changes and commit (hook runs automatically)
git add .
git commit  # commit_check.py runs via pre-commit hook

# 6. Create PR
python .agent/skills/github-repo-bootstrap/scripts/create_pr.py

# 7. Review PR
python .agent/skills/github-repo-bootstrap/scripts/review_pr.py

# 8. Merge PR
python .agent/skills/github-repo-bootstrap/scripts/merge_pr.py

# 9. View project status
python .agent/skills/github-repo-bootstrap/scripts/view_project.py
```

## 🧪 Testing

Run the unit test suite:

```bash
python .agent/skills/github-repo-bootstrap/tests/unit/test_commit_check.py
```

## License
MIT
