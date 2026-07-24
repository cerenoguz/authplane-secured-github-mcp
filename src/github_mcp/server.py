from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from github_mcp.github_client import GitHubClient


mcp = FastMCP("github-mcp")
github = GitHubClient()


@mcp.tool()
async def get_repository(
    owner: str,
    repository: str,
) -> dict:
    """Get information about a GitHub repository."""

    result = await github.get_repository(owner, repository)

    return {
        "full_name": result.get("full_name"),
        "description": result.get("description"),
        "html_url": result.get("html_url"),
        "default_branch": result.get("default_branch"),
        "visibility": result.get("visibility"),
        "stars": result.get("stargazers_count"),
        "forks": result.get("forks_count"),
        "open_issues": result.get("open_issues_count"),
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
