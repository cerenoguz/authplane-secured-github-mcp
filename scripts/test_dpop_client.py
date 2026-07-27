from __future__ import annotations

import asyncio
import json

import httpx
from authplane import (
    ASCredentials,
    AuthplaneClient,
    DPoPKeyMaterial,
    DPoPProvider,
)
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


AUTHPLANE_ISSUER = "http://localhost:9000"
MCP_URL = "http://localhost:8000/mcp"
RESOURCE_URI = "http://localhost:8000"
SCOPES = [
    "repo.read",
    "issues.read",
    "pulls.read",
    "users.read",
]


async def main() -> None:
    with open(".authplane-client.json") as file:
        credentials = json.load(file)

    private_key = ec.generate_private_key(ec.SECP256R1())
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    dpop = DPoPProvider(
        DPoPKeyMaterial.from_pem(private_key_pem)
    )

    authplane = await AuthplaneClient.create(
        issuer=AUTHPLANE_ISSUER,
        auth=ASCredentials(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
        ),
        dpop=dpop,
        dev_mode=True,
    )

    try:
        token_result = await authplane.client_credentials(
            scopes=SCOPES,
            resources=[RESOURCE_URI],
        )

        access_token = token_result.access_token

        print("Token type:", token_result.token_type)
        print("DPoP token received:", token_result.token_type.lower() == "dpop")

        async with httpx.AsyncClient(timeout=20.0) as http:
            def request_headers() -> dict[str, str]:
                return {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    **authplane.dpop_headers(
                        "POST",
                        MCP_URL,
                        access_token=access_token,
                    ),
                }

            initialize = await http.post(
                MCP_URL,
                headers=request_headers(),
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "github-dpop-client",
                            "version": "1.0",
                        },
                    },
                },
            )

            print("Initialize status:", initialize.status_code)
            print(initialize.text)
            initialize.raise_for_status()

            session_id = initialize.headers["mcp-session-id"]

            initialized_headers = request_headers()
            initialized_headers["Mcp-Session-Id"] = session_id

            initialized = await http.post(
                MCP_URL,
                headers=initialized_headers,
                json={
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                },
            )
            initialized.raise_for_status()

            tool_headers = request_headers()
            tool_headers["Mcp-Session-Id"] = session_id

            tool_response = await http.post(
                MCP_URL,
                headers=tool_headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "get_repository",
                        "arguments": {
                            "owner": "cerenoguz",
                            "repository": "authplane-secured-github-mcp",
                        },
                    },
                },
            )

            print("\nTool status:", tool_response.status_code)
            print(tool_response.text)
            tool_response.raise_for_status()
    finally:
        await authplane.aclose()


if __name__ == "__main__":
    asyncio.run(main())
