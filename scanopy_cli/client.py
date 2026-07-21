"""Scanopy API client."""

from __future__ import annotations

import requests
from typing import Any


class ServiceError(Exception):
    """Error communicating with the Scanopy API."""


class ServiceClient:
    """Thin wrapper around the Scanopy REST API."""

    def __init__(
        self,
        base_url: str = "http://localhost:60072",
        api_key: str = "",
        timeout: int = 10,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})
        if api_key:
            self._session.headers["Authorization"] = f"Bearer {api_key}"

    # ── low-level helpers ────────────────────────────────────────────

    def _get(
        self,
        path: str,
        params: dict | None = None,
        raw: bool = False,
    ) -> Any:
        """GET request with error handling.

        Returns parsed JSON (dict/list) or raw text when *raw=True*.
        Raises :class:`ServiceError` on any transport / protocol failure.
        """
        url = f"{self.base_url}{path}"
        try:
            resp = self._session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            if raw:
                return resp.text
            if not resp.content:
                return {}
            return resp.json()
        except requests.ConnectionError:
            raise ServiceError(
                f"Cannot connect to {self.base_url}. Is Scanopy running?"
            )
        except requests.Timeout:
            raise ServiceError(f"Timeout after {self.timeout}s: {url}")
        except (
            requests.HTTPError,
            requests.exceptions.ChunkedEncodingError,
        ) as exc:
            raise ServiceError(f"HTTP error: {exc}")
        except ValueError:
            raise ServiceError(f"Invalid JSON from {url}")

    def _get_paginated(
        self,
        path: str,
        limit: int = 0,
        offset: int = 0,
    ) -> dict:
        """GET with pagination support.

        Returns the full API envelope ``{"success": ..., "data": ..., "meta": ...}``.
        When *limit* > 0 the ``limit`` and ``offset`` query params are sent.
        """
        params: dict[str, Any] = {}
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        return self._get(path, params=params or None)

    # ── public API methods ───────────────────────────────────────────

    def ping(self) -> bool:
        """Return *True* if the server is reachable and healthy."""
        try:
            resp = self._get("/api/health")
            return bool(resp.get("success"))
        except ServiceError:
            return False

    def health(self) -> dict:
        """Return the raw health response envelope."""
        return self._get("/api/health")

    def info(self) -> dict:
        """Return server info derived from the health endpoint."""
        return self._get("/api/health")

    def list_hosts(
        self,
        limit: int = 0,
        offset: int = 0,
    ) -> dict:
        """Return hosts envelope (success, data, meta)."""
        return self._get_paginated("/api/hosts", limit=limit, offset=offset)

    def get_host(self, host_id: int | str) -> dict:
        """Return a single host by numeric ID.

        Note: the Scanopy API doesn't have a dedicated single-host endpoint,
        so we fetch all hosts and filter client-side.
        """
        envelope = self._get_paginated("/api/hosts")
        hosts = envelope.get("data", [])
        if isinstance(hosts, list):
            for host in hosts:
                if str(host.get("id")) == str(host_id):
                    return {"success": True, "data": host}
        raise ServiceError(f"Host '{host_id}' not found")

    def list_services(
        self,
        limit: int = 0,
        offset: int = 0,
    ) -> dict:
        """Return services envelope (success, data, meta)."""
        return self._get_paginated("/api/services", limit=limit, offset=offset)

    def search(self, query: str) -> dict:
        """Search hosts and services whose name, IP, or MAC contains *query*.

        Returns ``{"hosts": [...], "services": [...]}``.
        """
        q = query.lower()
        results: dict[str, list] = {"hosts": [], "services": []}

        # search hosts
        try:
            hosts_env = self._get_paginated("/api/hosts")
            for host in hosts_env.get("data", []):
                if self._host_matches(host, q):
                    results["hosts"].append(host)
        except ServiceError:
            pass

        # search services
        try:
            svc_env = self._get_paginated("/api/services")
            for svc in svc_env.get("data", []):
                if self._svc_matches(svc, q):
                    results["services"].append(svc)
        except ServiceError:
            pass

        return results

    # ── private search helpers ───────────────────────────────────────

    @staticmethod
    def _host_matches(host: dict, q: str) -> bool:
        if q in (host.get("name") or "").lower():
            return True
        for iface in host.get("interfaces", []):
            mac = iface.get("mac") or iface.get("mac_address") or ""
            if q in mac.lower():
                return True
        for ip_entry in host.get("ip_addresses", []):
            ip = ip_entry.get("ip") or ip_entry.get("ip_address") or ""
            if q in ip.lower():
                return True
            if q in (ip_entry.get("name") or "").lower():
                return True
        return False

    @staticmethod
    def _svc_matches(svc: dict, q: str) -> bool:
        for key in ("name", "service_name", "service_definition", "definition", "host_id"):
            if q in (svc.get(key) or "").lower():
                return True
        return False
