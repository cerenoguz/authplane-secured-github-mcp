from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from github_mcp.github_client import GitHubClient


mcp = FastMCP("github-mcp")
github = GitHubClient()


def repository_summary(repository: dict[str, Any]) -> dict[str, Any]:
    return {
        "full_name": repository.get("full_name"),
        "description": repository.get("description"),
        "html_url": repository.get("html_url"),
        "default_branch": repository.get("default_branch"),
        "visibility": repository.get("visibility"),
        "stars": repository.get("stargazers_count"),
        "forks": repository.get("forks_count"),
        "open_issues": repository.get("open_issues_count"),
    }


@mcp.tool()
async def get_repository(
    owner: str,
    repository: str,
) -> dict[str, Any]:
    """Get information about a GitHub repository."""

    result = await github.get_repository(owner, repository)
    return repository_summary(result)


@mcp.tool()
async def list_issues(
    owner: str,
    repository: str,
    state: str = "open",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """List issues from a GitHub repository."""

    issues = await github.list_issues(
        owner=owner,
        repository=repository,
        state=state,
        limit=limit,
    )

    return [
        {
            "number": issue.get("number"),
            "title": issue.get("title"),
            "state": issue.get("state"),
            "html_url": issue.get("html_url"),
            "author": issue.get("user", {}).get("login"),
            "created_at": issue.get("created_at"),
            "is_pull_request": "pull_request" in issue,
        }
        for issue in issues
    ]


@mcp.tool()
async def list_pull_requests(
    owner: str,
    repository: str,
    state: str = "open",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """List pull requests from a GitHub repository."""

    pulls = await github.list_pull_requests(
        owner=owner,
        repository=repository,
        state=state,
        limit=limit,
    )

    return [
        {
            "number": pull.get("number"),
            "title": pull.get("title"),
            "state": pull.get("state"),
            "html_url": pull.get("html_url"),
            "author": pull.get("user", {}).get("login"),
            "created_at": pull.get("created_at"),
        }
        for pull in pulls
    ]


@mcp.tool()
async def list_commits(
    owner: str,
    repository: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """List recent commits from a GitHub repository."""

    commits = await github.list_commits(
        owner=owner,
        repository=repository,
        limit=limit,
    )

    return [
        {
            "sha": commit.get("sha"),
            "message": (
                commit.get("commit", {})
                .get("message", "")
                .splitlines()[0]
            ),
            "author": (
                commit.get("commit", {})
                .get("author", {})
                .get("name")
            ),
            "date": (
                commit.get("commit", {})
                .get("author", {})
                .get("date")
            ),
            "html_url": commit.get("html_url"),
        }
        for commit in commits
    ]


@mcp.tool()
async def search_repositories(
    query: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search public GitHub repositories."""

    result = await github.search_repositories(
        query=query,
        limit=limit,
    )

    return [
        repository_summary(repository)
        for repository in result.get("items", [])
    ]


@mcp.tool()
async def get_user(
    username: str,
) -> dict[str, Any]:
    """Get public information about a GitHub user."""

    user = await github.get_user(username)

    return {
        "login": user.get("login"),
        "name": user.get("name"),
        "bio": user.get("bio"),
        "company": user.get("company"),
        "location": user.get("location"),
        "html_url": user.get("html_url"),
        "public_repositories": user.get("public_repos"),
        "followers": user.get("followers"),
        "following": user.get("following"),
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
