import os
import stat
import shutil
import subprocess
import re
from ..config import settings


def _force_remove_readonly(func, path, exc_info):
    """Windows fix: .git objects are read-only — force-remove them."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


class GitHubService:
    """Service to clone and manage GitHub repositories."""

    def __init__(self):
        self.clone_dir = settings.CLONE_DIR
        os.makedirs(self.clone_dir, exist_ok=True)

    def parse_repo_url(self, url: str) -> tuple:
        """Extract owner and repo name from a GitHub URL."""
        pattern = r"github\.com[/:]([^/]+)/([^/.]+)"
        match = re.search(pattern, url.rstrip("/"))
        if not match:
            raise ValueError(f"Invalid GitHub URL: {url}")
        return match.group(1), match.group(2)

    def clone_repo(self, repo_url: str, branch: str = "main", token: str = None) -> str:
        """Shallow-clone a repository and return the local path."""
        owner, repo_name = self.parse_repo_url(repo_url)
        local_path = os.path.join(self.clone_dir, f"{owner}_{repo_name}")

        # Clean up previous clone (Windows-safe)
        if os.path.exists(local_path):
            shutil.rmtree(local_path, onerror=_force_remove_readonly)

        # Build authenticated URL if token provided
        clone_url = repo_url
        if token:
            clone_url = repo_url.replace("https://", f"https://{token}@")

        # Shallow clone for speed
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", branch, clone_url, local_path],
                capture_output=True,
                text=True,
                check=True,
                timeout=120,
            )
        except subprocess.CalledProcessError:
            # Branch might be 'master' or default
            subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, local_path],
                capture_output=True,
                text=True,
                check=True,
                timeout=120,
            )

        return local_path

    def cleanup(self, local_path: str):
        """Remove a cloned repository (Windows-safe)."""
        if os.path.exists(local_path):
            shutil.rmtree(local_path, onerror=_force_remove_readonly)
