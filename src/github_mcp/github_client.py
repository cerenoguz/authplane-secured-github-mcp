from __future__ import annotations

from typing import Any

import httpx


GITHUB_API_BASE_URL = "https://api.github.com"


class GitHubClient:
    def __init__(self) -> None:
        self.base_url = GITHUB_API_BASE_URL

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "authplane-secured-github-mcp",
        }

    async def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"

        async with httpx.AsyncClient(
            headers=self._headers(),
            timeout=20.0,
        ) as client:
            response = await client.get(url, params=params)

        response.raise_for_status()
        return response.json()

    async def get_repository(
        self,
        owner: str,
        repository: str,
    ) -> dict[str, Any]:
        return await self._get(
            f"/repos/{owner}/{repository}"
        )

    async def list_issues(
        self,
        owner: str,
        repository: str,
        state: str = "open",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return await self._get(
            f"/repos/{owner}/{repository}/issues",
            params={
                "state": state,
                "per_page": limit,
            },
        )

    async def list_pull_requests(
        self,
        owner: str,
        repository: str,
        state: str = "open",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return await self._get(
            f"/repos/{owner}/{repository}/pulls",
            params={
                "state": state,
                "per_page": limit,
            },
        )

    async def list_commits(
        self,
        owner: str,
        repository: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return await self._get(
            f"/repos/{owner}/{repository}/commits",
            params={
                "per_page": limit,
            },
        )

    async def search_repositories(
        self,
        query: str,
        limit: int = 10,
    ) -> dict[str, Any]:
        return await self._get(
            "/search/repositories",
            params={
                "q": query,
                "per_page": limit,
            },
        )

    async def get_user(
        self,
        username: str,
    ) -> dict[str, Any]:
        return await self._get(
            f"/users/{username}"
        )
