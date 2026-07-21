"""Output formatters — Rich tables with plain-text fallback."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

try:
    from rich.console import Console
    from rich.table import Table

    HAS_RICH = True
except ImportError:
    HAS_RICH = False

console = Console() if HAS_RICH else None


# ── helpers ──────────────────────────────────────────────────────────

def print_json(data: Any, pretty: bool = True) -> None:
    """Dump *data* as JSON to stdout."""
    kwargs: dict[str, Any] = {"default": str}
    if pretty:
        kwargs["indent"] = 2
    print(json.dumps(data, **kwargs))


def _ts_to_str(ts: int | float | str | None) -> str:
    if ts is None:
        return "—"
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
    except (ValueError, TypeError, OSError):
        return str(ts)


def _mac_fmt(mac: str | None) -> str:
    """Return MAC in uppercase colon-separated form, or —."""
    if not mac:
        return "—"
    clean = mac.replace("-", "").replace(":", "").upper()
    if len(clean) == 12:
        return ":".join(clean[i : i + 2] for i in range(0, 12, 2))
    return mac


def _first_ip(host: dict) -> str:
    """Return the first IP address from a host dict, or —."""
    ips = host.get("ip_addresses", [])
    if ips and isinstance(ips, list):
        return ips[0].get("ip_address") or ips[0].get("ip") or "—"
    return "—"


def _first_mac(host: dict) -> str:
    """Return the first MAC address from a host's ip_addresses, or —."""
    ips = host.get("ip_addresses", [])
    if ips and isinstance(ips, list):
        return _mac_fmt(ips[0].get("mac_address") or ips[0].get("mac"))
    return "—"


def _svc_count(host: dict) -> int:
    """Return number of services associated with a host."""
    return len(host.get("services", []))


# ── public printers ──────────────────────────────────────────────────

def print_health(data: dict, as_json: bool = False) -> None:
    """Print health / info response."""
    if as_json:
        print_json(data)
        return
    version = data.get("data", "unknown")
    success = data.get("success", False)
    status = "[green]OK[/]" if success and HAS_RICH else ("OK" if success else "FAIL")
    if HAS_RICH:
        console.print(f"  Scanopy Server : {version}")
        console.print(f"  Status         : {status}")
    else:
        print(f"  Scanopy Server : {version}")
        print(f"  Status         : {'OK' if success else 'FAIL'}")


def print_hosts(hosts: list[dict], as_json: bool = False) -> None:
    """Print a hosts table."""
    if as_json:
        print_json(hosts)
        return
    if HAS_RICH:
        t = Table(title=f"Hosts ({len(hosts)})")
        t.add_column("ID", style="cyan", no_wrap=True, max_width=36)
        t.add_column("Name", style="bold")
        t.add_column("IP")
        t.add_column("MAC")
        t.add_column("Services", justify="right")
        for h in hosts:
            t.add_row(
                str(h.get("id", "")),
                h.get("name") or "—",
                _first_ip(h),
                _first_mac(h),
                str(_svc_count(h)),
            )
        console.print(t)
    else:
        print(f"Hosts ({len(hosts)}):")
        for h in hosts:
            print(
                f"  {h.get('id')}  {h.get('name') or '—':20s}  "
                f"{_first_ip(h):16s}  {_first_mac(h)}  svcs={_svc_count(h)}"
            )


def print_host_detail(host: dict, as_json: bool = False) -> None:
    """Print detailed host info with IPs, ports, services."""
    if as_json:
        print_json(host)
        return
    if HAS_RICH:
        console.print(
            f"[bold cyan]Host: {host.get('name', '—')}[/]  (id={host.get('id')})"
        )

        # IPs
        ips = host.get("ip_addresses", [])
        if ips:
            t = Table(title="IP Addresses")
            t.add_column("IP")
            t.add_column("Name")
            t.add_column("MAC")
            for entry in ips:
                t.add_row(
                    entry.get("ip_address") or entry.get("ip") or "—",
                    entry.get("name") or "—",
                    _mac_fmt(entry.get("mac_address") or entry.get("mac")),
                )
            console.print(t)

        # Ports
        ports = host.get("ports", [])
        if ports:
            t = Table(title="Ports")
            t.add_column("Port", justify="right")
            t.add_column("Protocol")
            t.add_column("Type")
            for entry in ports:
                t.add_row(
                    str(entry.get("number", "—")),
                    entry.get("protocol") or "—",
                    entry.get("type") or "—",
                )
            console.print(t)

        # Services
        services = host.get("services", [])
        if services:
            t = Table(title="Services")
            t.add_column("Name")
            t.add_column("Definition")
            for svc in services:
                t.add_row(
                    svc.get("name") or "—",
                    svc.get("service_definition") or svc.get("definition") or "—",
                )
            console.print(t)
    else:
        print(f"Host: {host.get('name', '—')} (id={host.get('id')})")
        for key in ("ip_addresses", "ports", "services"):
            vals = host.get(key, [])
            if vals:
                print(f"  {key}:")
                for v in vals:
                    print(f"    {v}")


def print_services(services: list[dict], as_json: bool = False) -> None:
    """Print a services table."""
    if as_json:
        print_json(services)
        return
    if HAS_RICH:
        t = Table(title=f"Services ({len(services)})")
        t.add_column("ID", style="cyan", no_wrap=True, max_width=36)
        t.add_column("Name", style="bold")
        t.add_column("Definition")
        t.add_column("Host ID")
        t.add_column("Bindings", justify="right")
        for s in services:
            t.add_row(
                str(s.get("id", "")),
                s.get("name") or "—",
                s.get("service_definition") or s.get("definition") or "—",
                (s.get("host_id") or "—")[:12] + "…"
                if s.get("host_id")
                else "—",
                str(len(s.get("bindings", []))),
            )
        console.print(t)
    else:
        print(f"Services ({len(services)}):")
        for s in services:
            print(
                f"  {s.get('id')}  {s.get('name') or '—':20s}  "
                f"{s.get('service_definition') or '—'}"
            )


def print_search_results(results: dict, as_json: bool = False) -> None:
    """Print combined search results (hosts + services)."""
    if as_json:
        print_json(results)
        return
    hosts = results.get("hosts", [])
    svcs = results.get("services", [])
    total = len(hosts) + len(svcs)
    if total == 0:
        msg = "No results found."
        if HAS_RICH:
            console.print(f"[yellow]{msg}[/]")
        else:
            print(msg)
        return
    if hosts:
        print_hosts(hosts, as_json=False)
    if svcs:
        if hosts:
            print()
        print_services(svcs, as_json=False)
