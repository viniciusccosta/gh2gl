import re
import subprocess

import keyring
import requests
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.text import Text
from rich.rule import Rule

# Create Rich console
console = Console()


def sanitize_project_name(name):
    """
    Sanitize repository name for GitLab project creation.

    GitLab project names must:
    - Be 1-255 characters long
    - Contain only letters, digits, '_', '.', dash, space
    - Not start or end with special characters
    - Not contain consecutive special characters
    - Not be reserved names like 'api', 'www', etc.
    """
    # Convert to lowercase for consistency
    sanitized = name.lower()

    # Replace invalid characters with dash
    sanitized = re.sub(r"[^a-z0-9._\-\s]", "-", sanitized)

    # Remove consecutive special characters
    sanitized = re.sub(r"[-._\s]{2,}", "-", sanitized)

    # Remove leading/trailing special characters
    sanitized = re.sub(r"^[-._\s]+|[-._\s]+$", "", sanitized)

    # Handle reserved names by adding suffix
    reserved_names = {
        "api",
        "www",
        "ftp",
        "mail",
        "pop",
        "smtp",
        "stage",
        "staging",
        "admin",
        "root",
    }
    if sanitized in reserved_names:
        sanitized = f"{sanitized}-project"

    # Ensure it's not empty and not too long
    if not sanitized:
        sanitized = "unnamed-project"
    elif len(sanitized) > 255:
        sanitized = sanitized[:255].rstrip("-._")

    # Ensure it doesn't start with a number (GitLab requirement)
    if sanitized and sanitized[0].isdigit():
        sanitized = f"project-{sanitized}"

    return sanitized


def mirror_repos(dry_run=False, skip_existing=False, force=False):
    # Welcome header
    console.print(Panel.fit(
        "[bold blue]🔄 GitHub to GitLab Mirror Tool[/bold blue]",
        border_style="blue"
    ))
    
    # Mode indicators
    modes = []
    if dry_run:
        modes.append("[yellow]🏃 DRY RUN MODE[/yellow] - No changes will be made")
    
    if skip_existing:
        modes.append("[cyan]⏭️  SKIP EXISTING MODE[/cyan] - Will skip existing repositories")
        
    if force:
        modes.append("[red]💪 FORCE MODE[/red] - Will overwrite existing GitLab repositories")
        
    if modes:
        console.print(Panel("\n".join(modes), title="[bold]Active Modes[/bold]", border_style="yellow"))
        
    # Validate conflicting options
    if skip_existing and force:
        console.print(Panel(
            "[red]❌ Error: Cannot use both --skip-existing and --force at the same time[/red]",
            title="[bold red]Configuration Error[/bold red]",
            border_style="red"
        ))
        return

    github_user = keyring.get_password("gh2gl", "github_username")
    github_token = keyring.get_password("gh2gl", "github_token")
    gitlab_url = keyring.get_password("gh2gl", "gitlab_url")
    gitlab_user = keyring.get_password("gh2gl", "gitlab_username")
    gitlab_token = keyring.get_password("gh2gl", "gitlab_token")

    # Validate credentials
    if not all([github_user, github_token, gitlab_url, gitlab_user, gitlab_token]):
        console.print(Panel(
            "[red]❌ Missing credentials. Please run the following commands first:[/red]\n\n"
            "[bold cyan]gh2gl login github[/bold cyan]\n"
            "[bold cyan]gh2gl login gitlab[/bold cyan]",
            title="[bold red]Authentication Required[/bold red]",
            border_style="red"
        ))
        return

    # Configuration table
    config_table = Table(show_header=True, header_style="bold magenta")
    config_table.add_column("Service", style="dim", width=12)
    config_table.add_column("Setting", style="dim", width=15) 
    config_table.add_column("Value", style="bold blue")
    
    config_table.add_row("GitHub", "Username", github_user)
    config_table.add_row("GitHub", "Token", "✅ Configured" if github_token else "❌ Missing")
    config_table.add_row("GitLab", "URL", gitlab_url)
    config_table.add_row("GitLab", "Username", gitlab_user)
    config_table.add_row("GitLab", "Token", "✅ Configured" if gitlab_token else "❌ Missing")
    
    console.print(Panel(config_table, title="[bold green]🔧 Configuration[/bold green]", border_style="green"))

    # --- 1. Get list of GitHub repos ---
    console.print(Rule("[bold blue]🔍 Discovering GitHub Repositories[/bold blue]"))
    
    with console.status("[bold green]Fetching repositories from GitHub API...") as status:
        headers = {"Authorization": f"token {github_token}"}
        repos = []
        page = 1

        while True:
            status.update(f"[bold green]Fetching page {page} from GitHub API...")
            r = requests.get(
                f"https://api.github.com/user/repos?per_page=100&page={page}&type=all",
                headers=headers,
            )

            data = r.json()
            if not data:
                break
            repos.extend([repo["name"] for repo in data])
            page += 1

    console.print(Panel(
        f"[bold green]✅ Discovered {len(repos)} repositories[/bold green]",
        title="[bold blue]📋 GitHub Discovery Complete[/bold blue]",
        border_style="green"
    ))

    # Track statistics
    stats = {
        "created": 0,
        "already_existed": 0,
        "skipped": 0,
        "forced_update": 0,
        "errors": 0,
        "mirrored": 0,
    }

    console.print(Rule("[bold blue]🚀 Processing Repositories[/bold blue]"))
    
    # --- 2. Create projects on GitLab ---
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        
        main_task = progress.add_task("[green]Processing repositories...", total=len(repos))
        
        for repo in repos:
            # Sanitize the repository name for GitLab
            sanitized_repo_name = sanitize_project_name(repo)
            repo_was_force_updated = False

            # Update progress with current repository
            progress.update(main_task, description=f"[green]Processing [bold]{repo}[/bold]...")
            
            console.print(f"\n[bold blue]📦 Processing {repo}[/bold blue]")
            if repo != sanitized_repo_name:
                console.print(f"  [yellow]🏷️  Sanitized name: {repo} → {sanitized_repo_name}[/yellow]")

            if dry_run:
                console.print(f"  [cyan]Would create project '[bold]{sanitized_repo_name}[/bold]' on GitLab at {gitlab_url}[/cyan]")
                if force:
                    console.print(f"  [red]Would force update existing GitLab repository with GitHub content[/red]")
                else:
                    console.print(f"  [green]Would mirror from GitHub to GitLab[/green]")
                progress.advance(main_task)
                continue

            # Create project on GitLab
            # Ensure gitlab_url doesn't have trailing slash
            gitlab_api_base = gitlab_url.rstrip("/")
            create_url = f"{gitlab_api_base}/api/v4/projects"

            headers = {"PRIVATE-TOKEN": gitlab_token}
            # Use both name and path to ensure consistency
            data = {
                "name": sanitized_repo_name,
                "path": sanitized_repo_name,
                "visibility": "private",
            }

            r = requests.post(create_url, headers=headers, data=data)

            if r.status_code == 201:
                console.print(f"  [green]✅ Created project {sanitized_repo_name} on GitLab.[/green]")
                stats["created"] += 1
            elif r.status_code == 400:
                try:
                    error_detail = r.json()
                    if (
                        ("message" in error_detail and "path" in error_detail["message"] and "already been taken" in str(error_detail["message"])) or
                        ("message" in error_detail and "name" in error_detail["message"] and "already been taken" in str(error_detail["message"]))
                    ):
                        # Both path and name conflicts mean the project already exists
                        console.print(f"  [yellow]📁 Project {sanitized_repo_name} already exists on GitLab.[/yellow]")
                        stats["already_existed"] += 1
                        if skip_existing:
                            console.print(f"  [cyan]⏭️  Skipping {sanitized_repo_name} (already exists)[/cyan]")
                            stats["skipped"] += 1
                            progress.advance(main_task)
                            continue
                        elif force:
                            console.print(f"  [red]💪 Force updating {sanitized_repo_name} with GitHub content[/red]")
                            stats["forced_update"] += 1
                            repo_was_force_updated = True
                            # Continue to git operations to force update
                        else:
                            # Default behavior: proceed with mirroring (sync)
                            pass
                    else:
                        console.print(f"  [red]❌ Error creating project {sanitized_repo_name}: {error_detail}[/red]")
                        stats["errors"] += 1
                        progress.advance(main_task)
                        continue
                except:
                    console.print(f"  [yellow]📁 Project {sanitized_repo_name} already exists on GitLab (400 response).[/yellow]")
                    stats["already_existed"] += 1
                    if skip_existing:
                        console.print(f"  [cyan]⏭️  Skipping {sanitized_repo_name} (already exists)[/cyan]")
                        stats["skipped"] += 1
                        progress.advance(main_task)
                        continue
                    elif force:
                        console.print(f"  [red]💪 Force updating {sanitized_repo_name} with GitHub content[/red]")
                        stats["forced_update"] += 1
                        repo_was_force_updated = True
                        # Continue to git operations to force update
                    else:
                        # Default behavior: proceed with mirroring (sync)
                        pass
            else:
                console.print(f"  [red]❌ Error creating project {sanitized_repo_name} (Status {r.status_code}): {r.text}[/red]")
                console.print(f"  [dim]API URL used: {create_url}[/dim]")
                stats["errors"] += 1
                progress.advance(main_task)
                continue

            # --- 3. Mirror repo from GitHub to GitLab ---
            github_clone_url = (
                f"https://{github_token}:x-oauth-basic@github.com/{github_user}/{repo}.git"
            )

            # Extract the base URL from gitlab_url (remove trailing slash if present)
            gitlab_base = gitlab_url.rstrip("/")
            if gitlab_base == "https://gitlab.com":
                gitlab_clone_url = f"https://oauth2:{gitlab_token}@gitlab.com/{gitlab_user}/{sanitized_repo_name}.git"
            else:
                # For self-hosted GitLab instances
                gitlab_clone_url = f"https://oauth2:{gitlab_token}@{gitlab_base.replace('https://', '')}/{gitlab_user}/{sanitized_repo_name}.git"

            # Use a temporary directory name based on the original repo name to avoid conflicts
            temp_dir = f"{repo}_temp_mirror"
            
            console.print(f"  [cyan]🔄 Cloning {repo} from GitHub...[/cyan]")
            clone_result = subprocess.run(["git", "clone", "--mirror", github_clone_url, temp_dir], 
                                          capture_output=True, text=True)
            
            if clone_result.returncode != 0:
                console.print(f"  [red]❌ Failed to clone {repo} from GitHub: {clone_result.stderr}[/red]")
                stats["errors"] += 1
                progress.advance(main_task)
                continue
                
            # Set the push URL to GitLab
            subprocess.run(
                ["git", "remote", "set-url", "--push", "origin", gitlab_clone_url],
                cwd=temp_dir,
            )
            
            # Push to GitLab
            push_args = ["git", "push", "--mirror"]
            if force:
                # In force mode, we want to ensure we overwrite everything
                push_args.extend(["--force"])
                console.print(f"  [red]💪 Force pushing to GitLab...[/red]")
            else:
                console.print(f"  [blue]📤 Pushing to GitLab...[/blue]")
                
            push_result = subprocess.run(push_args, cwd=temp_dir, capture_output=True, text=True)
            
            if push_result.returncode != 0:
                console.print(f"  [red]❌ Failed to push {repo} to GitLab: {push_result.stderr}[/red]")
                stats["errors"] += 1
            else:
                action = "Force updated" if repo_was_force_updated else "Mirrored"
                console.print(f"  [green]✅ {action} {repo} to GitLab as {sanitized_repo_name}.[/green]")
                stats["mirrored"] += 1
                
            # Clean up
            subprocess.run(["rm", "-rf", temp_dir])
            
            # Update progress
            progress.advance(main_task)

    console.print(Rule("[bold green]🎉 Mirroring Complete![/bold green]"))
    
    # Create summary table
    summary_table = Table(show_header=True, header_style="bold magenta")
    summary_table.add_column("Metric", style="dim", width=30)
    summary_table.add_column("Count", justify="right", style="bold cyan", width=10)
    
    summary_table.add_row("📋 Total", str(len(repos)))
    summary_table.add_row("✅ Created", str(stats['created']))
    summary_table.add_row("📁 Already existed", str(stats['already_existed']))
    summary_table.add_row("⏭️ Skipped", str(stats['skipped']))
    summary_table.add_row("💪 Force updated", str(stats['forced_update']))
    summary_table.add_row("🔄 Mirrored", str(stats['mirrored']))
    summary_table.add_row("❌ Errors", str(stats['errors']))
    
    console.print(Panel(summary_table, title="[bold green]📊 Summary[/bold green]", border_style="green"))

    # Additional messages
    messages = []
    if stats["errors"] > 0:
        messages.append(f"[red]⚠️  {stats['errors']} repositories had errors and were not mirrored.[/red]")
    if stats["mirrored"] > 0:
        messages.append(f"[green]🔗 Visit your GitLab profile: {gitlab_url.rstrip('/')}/{gitlab_user}[/green]")
    if stats["forced_update"] > 0:
        messages.append(f"[yellow]💪 {stats['forced_update']} existing repositories were force updated with latest GitHub content.[/yellow]")
    
    if messages:
        console.print(Panel("\n".join(messages), title="[bold blue]ℹ️ Additional Information[/bold blue]", border_style="blue"))
