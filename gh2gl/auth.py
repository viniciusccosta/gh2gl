# gh2gl/auth.py
from typing import Optional, Tuple

import keyring
import requests
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Create Rich console
console = Console()


def login_github():
    console.print(
        Panel.fit(
            "[bold blue]🐙 GitHub Authentication[/bold blue]", border_style="blue"
        )
    )

    username = typer.prompt("GitHub username")
    token = typer.prompt("GitHub personal access token", hide_input=True)

    keyring.set_password("gh2gl", "github_username", username)
    keyring.set_password("gh2gl", "github_token", token)

    console.print(
        Panel(
            "[green]✅ GitHub credentials saved securely.[/green]",
            title="[bold green]Success[/bold green]",
            border_style="green",
        )
    )


def login_gitlab():
    console.print(
        Panel.fit(
            "[bold orange1]🦊 GitLab Authentication[/bold orange1]",
            border_style="orange1",
        )
    )

    server_url = typer.prompt("GitLab instance URL", default="https://gitlab.com")
    username = typer.prompt("GitLab username")
    token = typer.prompt("GitLab personal access token", hide_input=True)

    keyring.set_password("gh2gl", "gitlab_url", server_url)
    keyring.set_password("gh2gl", "gitlab_username", username)
    keyring.set_password("gh2gl", "gitlab_token", token)

    console.print(
        Panel(
            "[green]✅ GitLab credentials saved securely.[/green]",
            title="[bold green]Success[/bold green]",
            border_style="green",
        )
    )


def get_github_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Get GitHub credentials from keyring."""
    username = keyring.get_password("gh2gl", "github_username")
    token = keyring.get_password("gh2gl", "github_token")
    return username, token


def get_gitlab_credentials() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Get GitLab credentials from keyring."""
    url = keyring.get_password("gh2gl", "gitlab_url")
    username = keyring.get_password("gh2gl", "gitlab_username")
    token = keyring.get_password("gh2gl", "gitlab_token")
    return url, username, token


def check_credentials_status() -> dict:
    """Check if credentials are configured."""
    github_username, github_token = get_github_credentials()
    gitlab_url, gitlab_username, gitlab_token = get_gitlab_credentials()

    return {
        "github": {
            "username_set": github_username is not None,
            "token_set": github_token is not None,
            "username": github_username if github_username else "Not set",
        },
        "gitlab": {
            "url_set": gitlab_url is not None,
            "username_set": gitlab_username is not None,
            "token_set": gitlab_token is not None,
            "url": gitlab_url if gitlab_url else "Not set",
            "username": gitlab_username if gitlab_username else "Not set",
        },
    }


def test_github_connection() -> Tuple[bool, str]:
    """Test GitHub API connection."""
    username, token = get_github_credentials()

    if not username or not token:
        return False, "GitHub credentials not configured"

    try:
        headers = {"Authorization": f"token {token}"}
        response = requests.get(
            "https://api.github.com/user", headers=headers, timeout=10
        )

        if response.status_code == 200:
            user_data = response.json()
            return True, f"Connected as {user_data.get('login', username)}"
        elif response.status_code == 401:
            return False, "Invalid GitHub token"
        else:
            return False, f"GitHub API error: {response.status_code}"
    except requests.RequestException as e:
        return False, f"Connection error: {str(e)}"


def test_gitlab_connection() -> Tuple[bool, str]:
    """Test GitLab API connection."""
    url, username, token = get_gitlab_credentials()

    if not url or not username or not token:
        return False, "GitLab credentials not configured"

    try:
        # Remove trailing slash if present
        base_url = url.rstrip("/")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{base_url}/api/v4/user", headers=headers, timeout=10)

        if response.status_code == 200:
            user_data = response.json()
            return True, f"Connected as {user_data.get('username', username)}"
        elif response.status_code == 401:
            return False, "Invalid GitLab token"
        else:
            return False, f"GitLab API error: {response.status_code}"
    except requests.RequestException as e:
        return False, f"Connection error: {str(e)}"
