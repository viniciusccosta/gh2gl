# gh2gl/cli.py
import typer

from gh2gl.auth import (
    check_credentials_status,
    login_github,
    login_gitlab,
    test_github_connection,
    test_gitlab_connection,
)
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


@app.command()
def status():
    """
    Show the status of configured credentials.
    """
    creds = check_credentials_status()

    typer.echo("🔍 Credentials Status:")
    typer.echo("")

    # GitHub status
    typer.echo("📘 GitHub:")
    typer.echo(f"  Username: {creds['github']['username']}")
    typer.echo(f"  Token: {'✅ Set' if creds['github']['token_set'] else '❌ Not set'}")
    typer.echo("")

    # GitLab status
    typer.echo("🦊 GitLab:")
    typer.echo(f"  URL: {creds['gitlab']['url']}")
    typer.echo(f"  Username: {creds['gitlab']['username']}")
    typer.echo(f"  Token: {'✅ Set' if creds['gitlab']['token_set'] else '❌ Not set'}")
    typer.echo("")

    # Overall readiness
    github_ready = creds["github"]["username_set"] and creds["github"]["token_set"]
    gitlab_ready = (
        creds["gitlab"]["url_set"]
        and creds["gitlab"]["username_set"]
        and creds["gitlab"]["token_set"]
    )

    if github_ready and gitlab_ready:
        typer.echo(
            "✨ All credentials configured! Run 'gh2gl test' to verify connections."
        )
    elif github_ready:
        typer.echo("⚠️  GitHub ready, GitLab credentials missing.")
    elif gitlab_ready:
        typer.echo("⚠️  GitLab ready, GitHub credentials missing.")
    else:
        typer.echo("❌ No credentials configured. Use 'gh2gl login' commands first.")


@app.command()
def test():
    """
    Test connectivity to GitHub and GitLab APIs.
    """
    typer.echo("🧪 Testing API connections...")
    typer.echo("")

    # Test GitHub
    typer.echo("📘 Testing GitHub connection...")
    github_success, github_msg = test_github_connection()
    if github_success:
        typer.echo(f"  ✅ {github_msg}")
    else:
        typer.echo(f"  ❌ {github_msg}")
    typer.echo("")

    # Test GitLab
    typer.echo("🦊 Testing GitLab connection...")
    gitlab_success, gitlab_msg = test_gitlab_connection()
    if gitlab_success:
        typer.echo(f"  ✅ {gitlab_msg}")
    else:
        typer.echo(f"  ❌ {gitlab_msg}")
    typer.echo("")

    # Summary
    if github_success and gitlab_success:
        typer.echo(
            "🎉 All connections successful! You're ready to mirror repositories."
        )
    elif github_success or gitlab_success:
        typer.echo("⚠️  Some connections failed. Check your credentials and try again.")
    else:
        typer.echo(
            "❌ All connections failed. Please check your credentials and network connection."
        )


if __name__ == "__main__":
    app()
