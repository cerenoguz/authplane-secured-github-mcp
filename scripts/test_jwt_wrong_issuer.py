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


WRONG_ISSUER = "http://localhost:9100"
EXPECTED_ISSUER = "http://localhost:9000"
RESOURCE = "http://localhost:8000"
MCP_URL = "http://localhost:8000/mcp"


async def main() -> None:
    with open(".authplane/wrong-issuer-client.json") as file:
        credentials = json.load(file)

    private_key = ec.generate_private_key(ec.SECP256R1())
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    authplane = await AuthplaneClient.create(
        issuer=WRONG_ISSUER,
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
            resources=[RESOURCE],
        )

        access_token = token_result.access_token

        response = httpx.post(
            MCP_URL,
            headers={
                "Authorization": f"DPoP {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                **authplane.dpop_headers(
                    "POST",
                    MCP_URL,
                    access_token=access_token,
                ),
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "wrong-issuer-test",
                        "version": "1.0",
                    },
                },
            },
        )

        print("Token issuer:", WRONG_ISSUER)
        print("Expected issuer:", EXPECTED_ISSUER)
        print("Token audience:", RESOURCE)
        print("Status:", response.status_code)
        print("Rejected as expected:", response.status_code == 401)
        print("Response:", response.text)

    finally:
        await authplane.aclose()


if __name__ == "__main__":
    asyncio.run(main())
