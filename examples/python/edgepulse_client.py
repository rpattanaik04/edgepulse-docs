"""A minimal EdgePulse API client that handles access tokens for you."""

import os

import requests


class EdgePulseError(Exception):
    """Raised when the API returns an error response."""

    def __init__(self, status, code, message, details=None):
        super().__init__(f"{status} {code}: {message}")
        self.status = status
        self.code = code
        self.message = message
        self.details = details or []


class EdgePulseClient:
    def __init__(self, base_url=None, client_id=None, client_secret=None):
        self.base_url = (base_url or os.getenv("EDGEPULSE_URL", "http://localhost:8000")).rstrip("/")
        self.client_id = client_id or os.getenv("EDGEPULSE_CLIENT_ID", "demo-client")
        self.client_secret = client_secret or os.getenv("EDGEPULSE_CLIENT_SECRET", "demo-secret")
        self._token = None
        self._session = requests.Session()

    def _send(self, method, path, use_token=True, **kwargs):
        headers = {"Authorization": f"Bearer {self._token}"} if use_token and self._token else {}
        # A long timeout allows a free-tier host to wake up after being idle.
        response = self._session.request(
            method, self.base_url + path, headers=headers, timeout=90, **kwargs
        )
        if response.status_code == 204:
            return None
        body = response.json()
        if not response.ok:
            error = body["error"]
            raise EdgePulseError(response.status_code, error["code"], error["message"], error.get("details"))
        return body

    def _authenticate(self):
        body = {"client_id": self.client_id, "client_secret": self.client_secret}
        self._token = self._send("POST", "/api/v1/auth/token", use_token=False, json=body)["access_token"]

    def request(self, method, path, **kwargs):
        """Send a request. Gets a token first, and gets a new one if the token expired."""
        if self._token is None:
            self._authenticate()
        try:
            return self._send(method, path, **kwargs)
        except EdgePulseError as error:
            if error.code != "unauthorized":
                raise
            self._authenticate()  # The token expired. Get a new one and retry once.
            return self._send(method, path, **kwargs)

    def pages(self, path, params=None, page_size=100):
        """Yield every item from a paged list endpoint."""
        offset = 0
        while True:
            query = {**(params or {}), "limit": page_size, "offset": offset}
            page = self.request("GET", path, params=query)
            yield from page["items"]
            offset += page_size
            if offset >= page["total"]:
                break
