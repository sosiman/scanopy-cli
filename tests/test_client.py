"""Tests for scanopy_cli.client."""

from __future__ import annotations

import json

import pytest

from scanopy_cli.client import ServiceClient, ServiceError


# ── fixtures ─────────────────────────────────────────────────────────


@pytest.fixture()
def client():
    """Return a ServiceClient pointing at a non-existent server."""
    return ServiceClient(base_url="http://127.0.0.1:1", api_key="test", timeout=2)


# ── ping tests ───────────────────────────────────────────────────────


def test_ping_unreachable(client):
    """ping() returns False when server is unreachable."""
    assert client.ping() is False


# ── connection error ─────────────────────────────────────────────────


def test_get_connection_error(client):
    """_get raises ServiceError with a clean message on connection failure."""
    with pytest.raises(ServiceError, match="Cannot connect"):
        client._get("/api/health")


# ── init tests ───────────────────────────────────────────────────────


def test_init_strips_trailing_slash():
    c = ServiceClient(base_url="http://localhost:60072/")
    assert c.base_url == "http://localhost:60072"


def test_init_sets_auth_header():
    c = ServiceClient(api_key="scp_u_test123")
    assert c._session.headers["Authorization"] == "Bearer scp_u_test123"


def test_init_no_auth_header_when_empty():
    c = ServiceClient(api_key="")
    assert "Authorization" not in c._session.headers


# ── search helper tests ──────────────────────────────────────────────


def test_host_matches_by_name():
    host = {"name": "web-server-01", "interfaces": [], "ip_addresses": []}
    assert ServiceClient._host_matches(host, "web") is True
    assert ServiceClient._host_matches(host, "nope") is False


def test_host_matches_by_ip():
    host = {
        "name": "box",
        "interfaces": [],
        "ip_addresses": [{"ip": "10.0.0.5"}],
    }
    assert ServiceClient._host_matches(host, "10.0.0") is True


def test_host_matches_by_mac():
    host = {
        "name": "box",
        "interfaces": [{"mac": "AA:BB:CC:DD:EE:FF"}],
        "ip_addresses": [],
    }
    assert ServiceClient._host_matches(host, "aa:bb") is True


def test_svc_matches_by_name():
    svc = {"name": "nginx", "host_name": "web01"}
    assert ServiceClient._svc_matches(svc, "nginx") is True
    assert ServiceClient._svc_matches(svc, "apache") is False
