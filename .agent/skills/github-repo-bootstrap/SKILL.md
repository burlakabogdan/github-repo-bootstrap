---
name: github-repo-bootstrap
description: Setup GitHub repositories with standard labels/projects and assist with commit messages. Use when the user wants to "bootstrap" a repo, standardizes labels, create issues, creates PRs, or needs help writing a commit message in a standard format.
license: MIT
compatibility: Requires python3, pip, and internet access. The `gh` CLI or GITHUB_TOKEN environment variable is required for authentication.
---

# GitHub Repo Bootstrap & Commit Assistant

This skill helps standardizing GitHub repositories and development workflows.

## Capabilities

1.  **Bootstrap Repository**: Configures Issues, Labels, Templates, and user-level Project v2.
2.  **Commit Assistant**: Helps write Conventional Commits and links them to Issues.
3.  **Work Management**: Creates Issues and PRs with proper templates and Project linking.

## Usage

### 1. Bootstrap Repository
**When to use**: User assumes "setup this repo", "bootstrap repo", "configure github".
**Action**: Run `scripts/bootstrap.py`.

```bash
python scripts/bootstrap.py
```

### 2. Commit Assistant
**When to use**: User is about to commit, asks "help me commit", "write commit message".
**Action**: Run `scripts/commit_check.py`.

```bash
python scripts/commit_check.py
```

### 3. Create Issue
**When to use**: User wants to create a bug/task/ticket.
**Action**: Run `scripts/create_issue.py`.

```bash
python scripts/create_issue.py
```

### 4. Create Branch
**When to use**: User picked an issue and wants to start working (create branch).
**Action**: Run `scripts/create_branch.py`.

```bash
python scripts/create_branch.py
```

### 5. Create PR
**When to use**: User wants to submit changes (Pull Request).
**Action**: Run `scripts/create_pr.py`.

```bash
python scripts/create_pr.py
```

### 6. Sync / Recover
**When to use**: User mentions "offline", "sync status", "retry".
**Action**: Run `scripts/sync.py`.

```bash
python scripts/sync.py
```
