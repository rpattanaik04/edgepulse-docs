# EdgePulse demo API

A small, working REST API that backs the EdgePulse documentation. Data is fictional and held in memory. It resets whenever the server restarts.

## Prerequisites

- Python 3.10 or later

## Run locally

1. Open a terminal in the `api-demo` folder.
2. Create and activate a virtual environment.

    ```bash
    python -m venv .venv
    source .venv/bin/activate        # Windows: .venv\Scripts\activate
    ```

3. Install dependencies.

    ```bash
    pip install -r requirements.txt
    ```

4. Start the server.

    ```bash
    uvicorn app.main:app --port 8000
    ```

5. Open the user interfaces in a browser.

    | Page | Address |
    |---|---|
    | Dashboard | <http://localhost:8000/dashboard> |
    | Swagger UI | <http://localhost:8000/docs> |

For a full walkthrough, see the [quick start](../docs/quick-start/index.md).

## Try it

1. Request an access token.

    ```bash
    curl -X POST http://localhost:8000/api/v1/auth/token \
      -H "Content-Type: application/json" \
      -d '{"client_id": "demo-client", "client_secret": "demo-secret"}'
    ```

2. Call an endpoint with the token.

    ```bash
    curl http://localhost:8000/api/v1/devices \
      -H "Authorization: Bearer <access_token>"
    ```

## Demo credentials

| Field | Value |
|---|---|
| `client_id` | `demo-client` |
| `client_secret` | `demo-secret` |

These are public demo values. When you host the API, override them with the `EDGEPULSE_CLIENT_ID` and `EDGEPULSE_CLIENT_SECRET` environment variables.

## Run the tests

```bash
pytest
```

## Regenerate the OpenAPI specification

From the `api-demo` folder:

```bash
python -c "import yaml; from app.main import app; yaml.safe_dump(app.openapi(), open('../docs/api/openapi.yaml', 'w'), sort_keys=False)"
```
