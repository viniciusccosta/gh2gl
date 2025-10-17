# gh2gl/cli.py
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from gh2gl.auth import (
    check_credentials_status,
    login_github,
    login_gitlab,
    test_github_connection,
    test_gitlab_connection,
)
from gh2gl.mirror import mirror_repos

# Create Rich console
console = Console()

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
def mirror(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without making changes"
    ),
    skip_existing: bool = typer.Option(
        False, "--skip-existing", help="Skip repositories that already exist on GitLab"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Force sync existing GitLab repositories with GitHub (overwrite GitLab content)",
    ),
):
    """
    Mirror all GitHub repositories to GitLab.

    By default, this command will:
    - Create new GitLab projects for GitHub repositories that don't exist
    - Update existing GitLab repositories with new commits from GitHub

    Options:
    --dry-run: Preview what would be done without making changes
    --skip-existing: Skip repositories that already exist on GitLab
    --force: Force overwrite existing GitLab repositories with GitHub content

    Note: --skip-existing and --force cannot be used together.
    """
    mirror_repos(dry_run=dry_run, skip_existing=skip_existing, force=force)


@app.command()
def status():
    """
    Show the status of configured credentials.
    """
    console.print(
        Panel.fit("[bold cyan]🔍 Credentials Status[/bold cyan]", border_style="cyan")
    )

    creds = check_credentials_status()

    # Create status table
    status_table = Table(show_header=True, header_style="bold magenta")
    status_table.add_column("Service", style="dim", width=12)
    status_table.add_column("Setting", style="dim", width=15)
    status_table.add_column("Value", style="bold")
    status_table.add_column("Status", justify="center", width=10)

    # GitHub rows
    status_table.add_row(
        "📘 GitHub",
        "Username",
        creds["github"]["username"],
        "✅" if creds["github"]["username_set"] else "❌",
    )
    status_table.add_row(
        "",
        "Token",
        "******" if creds["github"]["token_set"] else "-",
        "✅" if creds["github"]["token_set"] else "❌",
    )

    # GitLab rows
    status_table.add_row(
        "🦊 GitLab",
        "URL",
        creds["gitlab"]["url"],
        "✅" if creds["gitlab"]["url_set"] else "❌",
    )
    status_table.add_row(
        "",
        "Username",
        creds["gitlab"]["username"],
        "✅" if creds["gitlab"]["username_set"] else "❌",
    )
    status_table.add_row(
        "",
        "Token",
        "******" if creds["gitlab"]["token_set"] else "",
        "✅" if creds["gitlab"]["token_set"] else "❌",
    )

    console.print(status_table)

    # Overall readiness
    github_ready = creds["github"]["username_set"] and creds["github"]["token_set"]
    gitlab_ready = (
        creds["gitlab"]["url_set"]
        and creds["gitlab"]["username_set"]
        and creds["gitlab"]["token_set"]
    )

    if github_ready and gitlab_ready:
        console.print(
            Panel(
                "[green]✨ All credentials configured! Run '[bold cyan]gh2gl test[/bold cyan]' to verify connections.[/green]",
                title="[bold green]Ready[/bold green]",
                border_style="green",
            )
        )
    elif github_ready:
        console.print(
            Panel(
                "[yellow]⚠️  GitHub ready, GitLab credentials missing.[/yellow]",
                title="[bold yellow]Partial Setup[/bold yellow]",
                border_style="yellow",
            )
        )
    elif gitlab_ready:
        console.print(
            Panel(
                "[yellow]⚠️  GitLab ready, GitHub credentials missing.[/yellow]",
                title="[bold yellow]Partial Setup[/bold yellow]",
                border_style="yellow",
            )
        )
    else:
        console.print(
            Panel(
                "[red]❌ No credentials configured. Use '[bold cyan]gh2gl login[/bold cyan]' commands first.[/red]",
                title="[bold red]Setup Required[/bold red]",
                border_style="red",
            )
        )


@app.command()
def test():
    """
    Test connectivity to GitHub and GitLab APIs.
    """
    console = Console()

    console.print(
        Panel(
            "[bold cyan]🧪 Testing API Connections[/bold cyan]",
            title="[bold]Connection Test[/bold]",
            border_style="cyan",
        )
    )

    # Create table for results
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Service", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")
    table.add_column("Details", style="dim")

    console.print("\n[bold]Testing connections...[/bold]\n")

    # Test GitHub
    with console.status("[bold green]Testing GitHub API...", spinner="dots"):
        github_success, github_msg = test_github_connection()

    if github_success:
        table.add_row(
            "📘 GitHub", "[green]✅ Connected[/green]", f"[dim]{github_msg}[/dim]"
        )
    else:
        table.add_row(
            "📘 GitHub", "[red]❌ Failed[/red]", f"[dim red]{github_msg}[/dim red]"
        )

    # Test GitLab
    with console.status("[bold orange3]Testing GitLab API...", spinner="dots"):
        gitlab_success, gitlab_msg = test_gitlab_connection()

    if gitlab_success:
        table.add_row(
            "🦊 GitLab", "[green]✅ Connected[/green]", f"[dim]{gitlab_msg}[/dim]"
        )
    else:
        table.add_row(
            "🦊 GitLab", "[red]❌ Failed[/red]", f"[dim red]{gitlab_msg}[/dim red]"
        )

    console.print(table)
    console.print()

    # Summary panel
    if github_success and gitlab_success:
        console.print(
            Panel(
                "[bold green]🎉 All connections successful! You're ready to mirror repositories.[/bold green]",
                title="[bold green]Success[/bold green]",
                border_style="green",
            )
        )
    elif github_success or gitlab_success:
        console.print(
            Panel(
                "[bold yellow]⚠️  Some connections failed. Check your credentials and try again.[/bold yellow]",
                title="[bold yellow]Partial Success[/bold yellow]",
                border_style="yellow",
            )
        )
    else:
        console.print(
            Panel(
                "[bold red]❌ All connections failed. Please check your credentials and network connection.[/bold red]",
                title="[bold red]Connection Failed[/bold red]",
                border_style="red",
            )
        )


if __name__ == "__main__":
    app()
