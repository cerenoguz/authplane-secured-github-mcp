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


ISSUER = "http://localhost:9000"
WRONG_RESOURCE = "http://localhost:8100"
MCP_URL = "http://localhost:8000/mcp"


async def main() -> None:
    with open(".authplane-client.json") as file:
        credentials = json.load(file)

    private_key = ec.generate_private_key(ec.SECP256R1())
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    authplane = await AuthplaneClient.create(
        issuer=ISSUER,
        auth=ASCredentials(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
        ),
        dpop=DPoPProvider(
            DPoPKeyMaterial.from_pem(private_key_pem)
        ),
        dev_mode=True,
    )

    try:
        token_result = await authplane.client_credentials(
            scopes=["repo.read"],
            resources=[WRONG_RESOURCE],
        )

        access_token = token_result.access_token

        headers = {
            "Authorization": f"DPoP {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            **authplane.dpop_headers(
                "POST",
                MCP_URL,
                access_token=access_token,
            ),
        }

        response = httpx.post(
            MCP_URL,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "wrong-audience-test",
                        "version": "1.0",
                    },
                },
            },
        )

        print("Token audience:", WRONG_RESOURCE)
        print("MCP resource:", "http://localhost:8000")
        print("Status:", response.status_code)
        print("Rejected as expected:", response.status_code == 401)
        print("Response:", response.text)

    finally:
        await authplane.aclose()


if __name__ == "__main__":
    asyncio.run(main())
