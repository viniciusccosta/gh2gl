import subprocess

import keyring
import requests


def mirror_repos():
    github_user = keyring.get_password("gh2gl", "github_username")
    github_token = keyring.get_password("gh2gl", "github_token")
    gitlab_url = keyring.get_password("gh2gl", "gitlab_url")
    gitlab_user = keyring.get_password("gh2gl", "gitlab_username")
    gitlab_token = keyring.get_password("gh2gl", "gitlab_token")

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

    # --- 2. Create projects on GitLab ---
    for repo in repos:
        print(f"\nProcessing {repo}...")

        # Create project on GitLab
        r = requests.post(
            f"{gitlab_url}/api/v4/projects",
            headers={"PRIVATE-TOKEN": gitlab_token},
            data={"name": repo, "visibility": "private"},
        )
        if r.status_code == 201:
            print(f"Created project {repo} on GitLab.")
        elif r.status_code == 400:
            print(f"Project {repo} already exists on GitLab.")
        else:
            print(f"Error creating project {repo}: {r.text}")
            continue

        # --- 3. Mirror repo from GitHub to GitLab ---
        github_url = (
            f"https://{github_token}:x-oauth-basic@github.com/{github_user}/{repo}.git"
        )
        gitlab_url = (
            f"https://oauth2:{gitlab_token}@gitlab.com/{gitlab_user}/{repo}.git"
        )

        subprocess.run(["git", "clone", "--mirror", github_url, repo])
        subprocess.run(
            ["git", "remote", "set-url", "--push", "origin", gitlab_url], cwd=repo
        )
        subprocess.run(["git", "push", "--mirror"], cwd=repo)
        subprocess.run(["rm", "-rf", repo])
        print(f"Mirrored {repo} to GitLab.")
