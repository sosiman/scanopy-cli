"""Fetch Mermaid export from Scanopy server."""

from __future__ import annotations


def fetch_server_mermaid(client, topology_id: str, view: str = "L3Logical") -> str:
    """Get Mermaid export directly from the Scanopy API."""
    resp = client._get(
        f"/api/v1/topology/{topology_id}/export/mermaid",
        params={"view": view},
        raw=True,
    )
    if isinstance(resp, str) and "flowchart" in resp:
        return resp
    # Fallback to local generation
    return ""
