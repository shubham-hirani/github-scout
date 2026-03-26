import os
import httpx
from fastmcp import FastMCP

# Initialize FastMCP
mcp = FastMCP("GitHub-Scout")

# Use token if available
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


@mcp.tool()
async def get_repo_summary(owner: str, repo: str) -> str:
    """Fetches the latest 3 commits from a GitHub repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=3"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "User-Agent": "MCP-Scout-Agent"
    } if GITHUB_TOKEN else {"User-Agent": "MCP-Scout-Agent"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code != 200:
                return f"Error: GitHub API returned {response.status_code}"

            commits = response.json()
            if not commits:
                return "No commits found for this repository."

            msgs = [f"- {c['commit']['message']} (by {c['commit']['author']['name']})" for c in commits]
            return f"Recent activity in {owner}/{repo}:\n" + "\n".join(msgs)
        except Exception as e:
            return f"Failed to fetch data: {str(e)}"


if __name__ == "__main__":
    mcp.run()