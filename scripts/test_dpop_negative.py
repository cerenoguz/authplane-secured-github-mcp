from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import time
import uuid

import httpx
import jwt
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
SCOPES = ["repo.read"]


def base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def public_jwk(
    private_key: ec.EllipticCurvePrivateKey,
) -> dict[str, str]:
    numbers = private_key.public_key().public_numbers()

    return {
        "kty": "EC",
        "crv": "P-256",
        "x": base64url(numbers.x.to_bytes(32, "big")),
        "y": base64url(numbers.y.to_bytes(32, "big")),
    }


def create_proof(
    private_key: ec.EllipticCurvePrivateKey,
    access_token: str,
    *,
    method: str = "POST",
    url: str = MCP_URL,
    issued_at: int | None = None,
) -> str:
    token_hash = base64url(
        hashlib.sha256(access_token.encode()).digest()
    )

    claims = {
        "jti": str(uuid.uuid4()),
        "htm": method,
        "htu": url,
        "iat": issued_at or int(time.time()),
        "ath": token_hash,
    }

    return jwt.encode(
        claims,
        private_key,
        algorithm="ES256",
        headers={
            "typ": "dpop+jwt",
            "jwk": public_jwk(private_key),
        },
    )


def initialize_body(request_id: int) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {
                "name": "dpop-negative-test",
                "version": "1.0",
            },
        },
    }


def headers(
    access_token: str,
    proof: str | None,
) -> dict[str, str]:
    result = {
        "Authorization": f"DPoP {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    if proof:
        result["DPoP"] = proof

    return result


def show_result(
    name: str,
    response: httpx.Response,
) -> None:
    print(f"{name}:")
    print("  Status:", response.status_code)
    print(
        "  Rejected as expected:",
        response.status_code == 401,
    )
    print("  Response:", response.text[:250])


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
        print()

        async with httpx.AsyncClient(timeout=20.0) as client:
            # 1. Missing proof
            missing = await client.post(
                MCP_URL,
                headers=headers(access_token, None),
                json=initialize_body(1),
            )
            show_result("1. Missing proof", missing)

            # 2. Replay an SDK-generated valid proof
            replay_headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                **authplane.dpop_headers(
                    "POST",
                    MCP_URL,
                    access_token=access_token,
                ),
            }

            first = await client.post(
                MCP_URL,
                headers=replay_headers,
                json=initialize_body(2),
            )

            second = await client.post(
                MCP_URL,
                headers=replay_headers,
                json=initialize_body(3),
            )

            print("\n2. Replay proof:")
            print("  First status:", first.status_code)
            print("  Replayed status:", second.status_code)
            print(
                "  Replay rejected as expected:",
                first.status_code == 200
                and second.status_code == 401,
            )
            print("  Response:", second.text[:250])

            # 3. Proof bound to a different URI
            wrong_uri_proof = create_proof(
                private_key,
                access_token,
                url="http://localhost:8000/wrong-path",
            )

            wrong_uri = await client.post(
                MCP_URL,
                headers=headers(
                    access_token,
                    wrong_uri_proof,
                ),
                json=initialize_body(4),
            )
            show_result("\n3. Wrong URI", wrong_uri)

            # 4. Proof says GET, but request is POST
            wrong_method_proof = create_proof(
                private_key,
                access_token,
                method="GET",
            )

            wrong_method = await client.post(
                MCP_URL,
                headers=headers(
                    access_token,
                    wrong_method_proof,
                ),
                json=initialize_body(5),
            )
            show_result("4. Wrong method", wrong_method)

            # 5. Proof timestamp is ten minutes old
            expired_proof = create_proof(
                private_key,
                access_token,
                issued_at=int(time.time()) - 600,
            )

            expired = await client.post(
                MCP_URL,
                headers=headers(
                    access_token,
                    expired_proof,
                ),
                json=initialize_body(6),
            )
            show_result("5. Expired proof", expired)

    finally:
        await authplane.aclose()


if __name__ == "__main__":
    asyncio.run(main())
