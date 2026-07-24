import pytest
import respx
from httpx import Response

from github_mcp.github_client import GitHubClient


@pytest.mark.asyncio
@respx.mock
async def test_get_repository():
    route = respx.get(
        "https://api.github.com/repos/cerenoguz/authplane-secured-github-mcp"
    ).mock(
        return_value=Response(
            200,
            json={
                "full_name": "cerenoguz/authplane-secured-github-mcp",
                "default_branch": "main",
            },
        )
    )

    client = GitHubClient()

    result = await client.get_repository(
        "cerenoguz",
        "authplane-secured-github-mcp",
    )

    assert route.called
    assert result["full_name"] == "cerenoguz/authplane-secured-github-mcp"
    assert result["default_branch"] == "main"


@pytest.mark.asyncio
@respx.mock
async def test_list_issues():
    route = respx.get(
        "https://api.github.com/repos/example/project/issues"
    ).mock(
        return_value=Response(
            200,
            json=[
                {
                    "number": 1,
                    "title": "Example issue",
                    "state": "open",
                }
            ],
        )
    )

    client = GitHubClient()

    result = await client.list_issues(
        "example",
        "project",
        limit=10,
    )

    assert route.called
    assert len(result) == 1
    assert result[0]["title"] == "Example issue"


@pytest.mark.asyncio
@respx.mock
async def test_github_error():
    respx.get(
        "https://api.github.com/repos/example/missing"
    ).mock(
        return_value=Response(
            404,
            json={"message": "Not Found"},
        )
    )

    client = GitHubClient()

    with pytest.raises(Exception):
        await client.get_repository(
            "example",
            "missing",
        )
