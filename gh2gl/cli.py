# gh2gl/cli.py
import typer

from gh2gl.auth import login_github, login_gitlab
from gh2gl.mirror import mirror_repos

app = typer.Typer()

login_app = typer.Typer()
app.add_typer(login_app, name="login", help="Login to services")


@login_app.command("github")
def login_github_cmd():
    login_github()


@login_app.command("gitlab")
def login_gitlab_cmd():
    login_gitlab()


@app.command()
def mirror():
    """
    Mirror all GitHub repositories to GitLab.
    """
    mirror_repos()


if __name__ == "__main__":
    app()
