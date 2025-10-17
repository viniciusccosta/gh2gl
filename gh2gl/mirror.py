import re
import subprocess

import keyring
import requests


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
    if dry_run:
        print("🏃 DRY RUN MODE - No changes will be made")
        print()

    if skip_existing:
        print("⏭️  SKIP EXISTING MODE - Will skip repositories that already exist")
        print()
        
    if force:
        print("💪 FORCE MODE - Will overwrite existing GitLab repositories with GitHub content")
        print()
        
    # Validate conflicting options
    if skip_existing and force:
        print("❌ Error: Cannot use both --skip-existing and --force at the same time")
        return

    github_user = keyring.get_password("gh2gl", "github_username")
    github_token = keyring.get_password("gh2gl", "github_token")
    gitlab_url = keyring.get_password("gh2gl", "gitlab_url")
    gitlab_user = keyring.get_password("gh2gl", "gitlab_username")
    gitlab_token = keyring.get_password("gh2gl", "gitlab_token")

    # Validate credentials
    if not all([github_user, github_token, gitlab_url, gitlab_user, gitlab_token]):
        print(
            "❌ Missing credentials. Please run 'gh2gl login github' and 'gh2gl login gitlab' first."
        )
        return

    print(f"🔧 Configuration:")
    print(f"  GitHub user: {github_user}")
    print(f"  GitLab URL: {gitlab_url}")
    print(f"  GitLab user: {gitlab_user}")
    print()

    # --- 1. Get list of GitHub repos ---
    headers = {"Authorization": f"token {github_token}"}
    repos = []
    page = 1

    while True:
        r = requests.get(
            f"https://api.github.com/users/{github_user}/repos?per_page=100&page={page}",
            headers=headers,
        )

        data = r.json()
        if not data:
            break
        repos.extend([repo["name"] for repo in data])
        page += 1

    print(f"Found {len(repos)} repositories on GitHub.")

    # Track statistics
    stats = {
        "created": 0,
        "already_existed": 0,
        "skipped": 0,
        "forced_update": 0,
        "errors": 0,
        "mirrored": 0,
    }

    # --- 2. Create projects on GitLab ---
    for repo in repos:
        # Sanitize the repository name for GitLab
        sanitized_repo_name = sanitize_project_name(repo)
        repo_was_force_updated = False

        print(f"\nProcessing {repo}...")
        if repo != sanitized_repo_name:
            print(f"  Sanitized name: {repo} → {sanitized_repo_name}")

        if dry_run:
            print(
                f"  Would create project '{sanitized_repo_name}' on GitLab at {gitlab_url}"
            )
            if force:
                print(f"  Would force update existing GitLab repository with GitHub content")
            else:
                print(f"  Would mirror from GitHub to GitLab")
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
            print(f"Created project {sanitized_repo_name} on GitLab.")
            stats["created"] += 1
        elif r.status_code == 400:
            try:
                error_detail = r.json()
                if (
                    ("message" in error_detail and "path" in error_detail["message"] and "already been taken" in str(error_detail["message"])) or
                    ("message" in error_detail and "name" in error_detail["message"] and "already been taken" in str(error_detail["message"]))
                ):
                    # Both path and name conflicts mean the project already exists
                    print(f"  Project {sanitized_repo_name} already exists on GitLab.")
                    stats["already_existed"] += 1
                    if skip_existing:
                        print(f"  ⏭️  Skipping {sanitized_repo_name} (already exists)")
                        stats["skipped"] += 1
                        continue
                    elif force:
                        print(f"  💪 Force updating {sanitized_repo_name} with GitHub content")
                        stats["forced_update"] += 1
                        repo_was_force_updated = True
                        # Continue to git operations to force update
                    else:
                        # Default behavior: proceed with mirroring (sync)
                        pass
                else:
                    print(
                        f"Error creating project {sanitized_repo_name}: {error_detail}"
                    )
                    stats["errors"] += 1
                    continue
            except:
                print(
                    f"  Project {sanitized_repo_name} already exists on GitLab (400 response)."
                )
                stats["already_existed"] += 1
                if skip_existing:
                    print(f"  ⏭️  Skipping {sanitized_repo_name} (already exists)")
                    stats["skipped"] += 1
                    continue
                elif force:
                    print(f"  💪 Force updating {sanitized_repo_name} with GitHub content")
                    stats["forced_update"] += 1
                    repo_was_force_updated = True
                    # Continue to git operations to force update
                else:
                    # Default behavior: proceed with mirroring (sync)
                    pass
        else:
            print(
                f"Error creating project {sanitized_repo_name} (Status {r.status_code}): {r.text}"
            )
            print(f"API URL used: {create_url}")
            print(f"Headers: {headers}")
            stats["errors"] += 1
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
        
        print(f"  🔄 Cloning {repo} from GitHub...")
        clone_result = subprocess.run(["git", "clone", "--mirror", github_clone_url, temp_dir], 
                                      capture_output=True, text=True)
        
        if clone_result.returncode != 0:
            print(f"  ❌ Failed to clone {repo} from GitHub: {clone_result.stderr}")
            stats["errors"] += 1
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
            print(f"  💪 Force pushing to GitLab...")
        else:
            print(f"  📤 Pushing to GitLab...")
            
        push_result = subprocess.run(push_args, cwd=temp_dir, capture_output=True, text=True)
        
        if push_result.returncode != 0:
            print(f"  ❌ Failed to push {repo} to GitLab: {push_result.stderr}")
            stats["errors"] += 1
        else:
            action = "Force updated" if repo_was_force_updated else "Mirrored"
            print(f"  ✅ {action} {repo} to GitLab as {sanitized_repo_name}.")
            stats["mirrored"] += 1
            
        # Clean up
        subprocess.run(["rm", "-rf", temp_dir])

    # --- 4. Print Summary ---
    print(f"\n🎉 Mirroring Complete!")
    print(f"📊 Summary:")
    print(f"  📋 Total repositories: {len(repos)}")
    print(f"  ✅ Created: {stats['created']}")
    print(f"  📁 Already existed: {stats['already_existed']}")
    print(f"  ⏭️ Skipped: {stats['skipped']}")
    print(f"  💪 Force updated: {stats['forced_update']}")
    print(f"  ✅ Mirrored: {stats['mirrored']}")
    print(f"  ❌ Errors: {stats['errors']}")

    if stats["errors"] > 0:
        print(f"\n⚠️  {stats['errors']} repositories had errors and were not mirrored.")
    if stats["mirrored"] > 0:
        print(f"\n🔗 Visit your GitLab profile to see the mirrored repositories:")
        print(f"   {gitlab_url.rstrip('/')}/{gitlab_user}")
    if stats["forced_update"] > 0:
        print(f"\n💪 {stats['forced_update']} existing repositories were force updated with latest GitHub content.")
