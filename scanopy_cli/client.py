"""Scanopy API client."""

from __future__ import annotations

import re
import requests
from typing import Any

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


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

    def config(self) -> dict:
        """Return public server configuration."""
        return self._get("/api/config")

    # ── hosts ────────────────────────────────────────────────────────

    def list_hosts(
        self,
        limit: int = 0,
        offset: int = 0,
    ) -> dict:
        """Return hosts envelope (success, data, meta)."""
        return self._get_paginated("/api/hosts", limit=limit, offset=offset)

    def get_host(self, host_id: int | str) -> dict:
        """Return a single host by ID.

        If *host_id* is a UUID, hits ``/api/v1/hosts/{id}`` directly.
        Otherwise falls back to fetching all hosts and filtering.
        """
        if _UUID_RE.match(str(host_id)):
            try:
                return self._get(f"/api/v1/hosts/{host_id}")
            except ServiceError:
                pass  # fall through to list-based lookup

        envelope = self._get_paginated("/api/hosts")
        hosts = envelope.get("data", [])
        if isinstance(hosts, list):
            for host in hosts:
                if str(host.get("id")) == str(host_id):
                    return {"success": True, "data": host}
        raise ServiceError(f"Host '{host_id}' not found")

    # ── services ─────────────────────────────────────────────────────

    def list_services(
        self,
        limit: int = 0,
        offset: int = 0,
    ) -> dict:
        """Return services envelope (success, data, meta)."""
        return self._get_paginated("/api/services", limit=limit, offset=offset)

    # ── search ───────────────────────────────────────────────────────

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

    # ── networks ─────────────────────────────────────────────────────

    def list_networks(self) -> dict:
        """Return networks envelope."""
        return self._get("/api/v1/networks")

    # ── subnets ──────────────────────────────────────────────────────

    def list_subnets(self, limit: int = 0, offset: int = 0) -> dict:
        """Return subnets envelope with pagination."""
        return self._get_paginated("/api/v1/subnets", limit=limit, offset=offset)

    # ── ports ────────────────────────────────────────────────────────

    def list_ports(self, limit: int = 0, offset: int = 0) -> dict:
        """Return ports envelope with pagination."""
        return self._get_paginated("/api/v1/ports", limit=limit, offset=offset)

    # ── IP addresses ─────────────────────────────────────────────────

    def list_ip_addresses(self, limit: int = 0, offset: int = 0) -> dict:
        """Return IP addresses envelope with pagination."""
        return self._get_paginated("/api/v1/ip-addresses", limit=limit, offset=offset)

    # ── tags ─────────────────────────────────────────────────────────

    def list_tags(self) -> dict:
        """Return tags envelope."""
        return self._get("/api/v1/tags")

    # ── VLANs ────────────────────────────────────────────────────────

    def list_vlans(self) -> dict:
        """Return VLANs envelope."""
        return self._get("/api/v1/vlans")

    # ── dependencies ─────────────────────────────────────────────────

    def list_dependencies(self) -> dict:
        """Return dependencies envelope."""
        return self._get("/api/v1/dependencies")

    # ── snapshots ────────────────────────────────────────────────────

    def list_snapshots(self) -> dict:
        """Return snapshots envelope."""
        return self._get("/api/v1/snapshots")

    # ── users ────────────────────────────────────────────────────────

    def list_users(self) -> dict:
        """Return users envelope."""
        return self._get("/api/v1/users")

    # ── organization ─────────────────────────────────────────────────

    def get_organization(self) -> dict:
        """Return organization info."""
        return self._get("/api/v1/organizations")

    # ── credentials ──────────────────────────────────────────────────

    def list_credentials(self) -> dict:
        """Return credentials envelope."""
        return self._get("/api/v1/credentials")

    # ── shares ───────────────────────────────────────────────────────

    def list_shares(self) -> dict:
        """Return shares envelope."""
        return self._get("/api/v1/shares")

    # ── topology ─────────────────────────────────────────────────────

    def topology_list(self) -> dict:
        """Return topology list envelope."""
        return self._get("/api/v1/topology")

    def topology_data(self, network_id: str) -> dict:
        """Return full topology data for a network."""
        return self._get(
            "/api/v1/topology/data",
            params={"network_id": network_id},
        )

    def topology_get(self, topology_id: str) -> dict:
        """Return a single topology by ID."""
        return self._get(f"/api/v1/topology/{topology_id}")

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
