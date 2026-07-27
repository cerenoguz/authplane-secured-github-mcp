```

### Components

- **MCP Client** registers through DCR or identifies itself through CIMD.
- **AuthPlane** issues OAuth access tokens and publishes signing keys.
- **GitHub MCP Server** validates authentication and checks tool scopes.
- **GitHub REST API** supplies repository and user data.

## OAuth Client Credentials and DPoP sequence

```mermaid
sequenceDiagram
    participant C as MCP Client
    participant A as AuthPlane
    participant M as GitHub MCP Server
    participant G as GitHub REST API

    C->>A: Register client through DCR or CIMD
    A-->>C: Client credentials
    C->>C: Generate DPoP key pair
    C->>A: Token request with credentials and DPoP proof
    A-->>C: DPoP-bound access token
    C->>M: Initialize with token and DPoP proof
    M->>M: Validate JWT and DPoP proof
    M-->>C: MCP session initialized
    C->>M: Invoke scoped MCP tool

    alt Scope is present
        M->>G: Call GitHub REST API
        G-->>M: GitHub data
        M-->>C: Successful result
    else Scope is missing
        M-->>C: Authorization error
    end
```

## Request validation order

For every protected MCP request, the server checks:

1. An access token is present.
2. A DPoP proof is present.
3. The JWT signature is trusted.
4. The issuer matches AuthPlane.
5. The audience matches the MCP resource URI.
6. The token has not expired.
7. The DPoP key matches the token.
8. The DPoP method and URI match the request.
9. The DPoP proof has not been replayed.
10. The token contains the required tool scope.
