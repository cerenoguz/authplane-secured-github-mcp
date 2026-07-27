# AuthPlane-Secured GitHub MCP Server

A GitHub REST API MCP server secured using AuthPlane.

## Features

- FastMCP server with six GitHub REST API tools
- OAuth 2.0 Client Credentials
- AuthPlane authorization server integration
- Dynamic Client Registration
- DPoP-bound access tokens
- Client ID Metadata Documents
- Scope-based authorization
- JWT claim validation
- Positive and negative security testing

## Status

Core implementation and security testing are complete. Documentation and architecture diagrams are in progress.


## Authentication and authorization

The MCP server is protected by AuthPlane and uses OAuth 2.0 Client Credentials for machine-to-machine authentication.

The implementation includes:

- Dynamic Client Registration (DCR)
- DPoP-bound access tokens
- Client ID Metadata Documents (CIMD)
- JWT issuer, audience, signature, and expiration validation
- Scope-based authorization for individual MCP tools

### Resource server

| Setting | Local value |
|---|---|
| AuthPlane issuer | `http://localhost:9000` |
| MCP resource URI | `http://localhost:8000` |
| MCP endpoint | `http://localhost:8000/mcp` |
| OAuth grant | `client_credentials` |
| Token type | `DPoP` |

### Tool scopes

| MCP tool | Required scope |
|---|---|
| `get_repository` | `repo.read` |
| `list_commits` | `repo.read` |
| `search_repositories` | `repo.read` |
| `list_issues` | `issues.read` |
| `list_pull_requests` | `pulls.read` |
| `get_user` | `users.read` |

A client can invoke only the tools allowed by the scopes in its access token. For example, a client with only `users.read` can call `get_user`, but receives an authorization error when calling `get_repository`.

## Security testing

The following authentication and authorization cases were tested against the protected MCP server.

| Test | Expected result | Result |
|---|---|---|
| Valid DPoP token | MCP initialization and tool call succeed | Passed |
| Missing DPoP proof | Request is rejected with `401` | Passed |
| Replayed DPoP proof | Reused proof is rejected with `401` | Passed |
| Wrong DPoP URI | Request is rejected with `401` | Passed |
| Wrong DPoP method | Request is rejected with `401` | Passed |
| Expired DPoP proof | Request is rejected with `401` | Passed |
| Invalid JWT signature | Token is rejected with `401` | Passed |
| Wrong JWT audience | Token is rejected with `401` | Passed |
| Wrong JWT issuer | Token is rejected with `401` | Passed |
| Expired access token | Token is rejected with `401` | Passed |
| Missing required scope | Tool call returns an authorization error | Passed |

### JWT claim validation

The MCP server accepts access tokens only when all of the following checks succeed:

- The token signature matches a trusted AuthPlane signing key.
- The `iss` claim matches the configured AuthPlane issuer.
- The `aud` claim contains the MCP resource URI.
- The token has not passed its `exp` time.
- The token contains the scope required by the requested MCP tool.
- The request includes a valid DPoP proof bound to the token, HTTP method, and request URI.

### Test scripts

| Script | Purpose |
|---|---|
| `scripts/test_dpop_client.py` | Valid DPoP authentication and MCP tool call |
| `scripts/test_dpop_negative.py` | Missing, replayed, incorrect, and expired DPoP proofs |
| `scripts/test_jwt_invalid_signature.py` | Invalid JWT signature rejection |
| `scripts/test_jwt_wrong_audience.py` | Wrong audience rejection |
| `scripts/test_jwt_wrong_issuer.py` | Wrong issuer rejection |
| `scripts/test_jwt_expired.py` | Expired access-token rejection |

The Authlib deprecation warning displayed during the tests originates from the current AuthPlane SDK dependency and does not affect the test results.
