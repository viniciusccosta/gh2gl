# gh2gl/auth.py
import keyring
import typer


def login_github():
    username = typer.prompt("GitHub username")
    token = typer.prompt("GitHub personal access token", hide_input=True)

    keyring.set_password("gh2gl", "github_username", username)
    keyring.set_password("gh2gl", "github_token", token)

    typer.echo("GitHub credentials saved securely.")


def login_gitlab():
    server_url = typer.prompt("GitLab instance URL", default="https://gitlab.com")
    username = typer.prompt("GitLab username")
    token = typer.prompt("GitLab personal access token", hide_input=True)

    keyring.set_password("gh2gl", "gitlab_url", server_url)
    keyring.set_password("gh2gl", "gitlab_username", username)
    keyring.set_password("gh2gl", "gitlab_token", token)

    typer.echo("GitLab credentials saved securely.")
