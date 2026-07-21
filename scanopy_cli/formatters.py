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


def _short_id(val: str | None, width: int = 12) -> str:
    if not val:
        return "—"
    return val[:width] + "…" if len(val) > width else val


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
                _short_id(s.get("host_id")),
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


# ── new printers ─────────────────────────────────────────────────────

def print_networks(data: list[dict] | dict, as_json: bool = False) -> None:
    """Print networks table."""
    items = data if isinstance(data, list) else data.get("data", [])
    if as_json:
        print_json(data)
        return
    if HAS_RICH:
        t = Table(title=f"Networks ({len(items)})")
        t.add_column("ID", style="cyan", no_wrap=True, max_width=36)
        t.add_column("Name", style="bold")
        t.add_column("Description")
        for n in items:
            t.add_row(
                str(n.get("id", "")),
                n.get("name") or "—",
                (n.get("description") or "—")[:60],
            )
        console.print(t)
    else:
        for n in items:
            print(f"  {n.get('id')}  {n.get('name') or '—'}")


def print_subnets(data: list[dict] | dict, as_json: bool = False) -> None:
    """Print subnets table."""
    items = data if isinstance(data, list) else data.get("data", [])
    if as_json:
        print_json(data)
        return
    if HAS_RICH:
        t = Table(title=f"Subnets ({len(items)})")
        t.add_column("ID", style="cyan", no_wrap=True, max_width=36)
        t.add_column("Name", style="bold")
        t.add_column("CIDR")
        t.add_column("VLAN")
        for s in items:
            t.add_row(
                str(s.get("id", "")),
                s.get("name") or "—",
                s.get("cidr") or s.get("subnet") or "—",
                str(s.get("vlan_id") or s.get("vlan") or "—"),
            )
        console.print(t)
    else:
        for s in items:
            print(f"  {s.get('id')}  {s.get('name') or '—'}  {s.get('cidr', '—')}")


def print_ports(data: list[dict] | dict, as_json: bool = False) -> None:
    """Print ports table."""
    items = data if isinstance(data, list) else data.get("data", [])
    if as_json:
        print_json(data)
        return
    if HAS_RICH:
        t = Table(title=f"Ports ({len(items)})")
        t.add_column("ID", style="cyan", no_wrap=True, max_width=36)
        t.add_column("Host", style="bold")
        t.add_column("Number", justify="right")
        t.add_column("Protocol")
        t.add_column("Type")
        for p in items:
            t.add_row(
                str(p.get("id", "")),
                _short_id(p.get("host_id")),
                str(p.get("number") or p.get("port") or "—"),
                p.get("protocol") or "—",
                p.get("type") or "—",
            )
        console.print(t)
    else:
        for p in items:
            print(f"  {p.get('number') or p.get('port')}/{p.get('protocol')} ({p.get('type', '—')})")


def print_ips(data: list[dict] | dict, as_json: bool = False) -> None:
    """Print IP addresses table."""
    items = data if isinstance(data, list) else data.get("data", [])
    if as_json:
        print_json(data)
        return
    if HAS_RICH:
        t = Table(title=f"IP Addresses ({len(items)})")
        t.add_column("ID", style="cyan", no_wrap=True, max_width=36)
        t.add_column("IP", style="bold")
        t.add_column("Host")
        t.add_column("Subnet")
        t.add_column("MAC")
        for ip in items:
            t.add_row(
                str(ip.get("id", "")),
                ip.get("ip") or ip.get("ip_address") or "—",
                _short_id(ip.get("host_id")),
                _short_id(ip.get("subnet_id")),
                _mac_fmt(ip.get("mac") or ip.get("mac_address")),
            )
        console.print(t)
    else:
        for ip in items:
            print(f"  {ip.get('ip') or ip.get('ip_address', '—')}  host={_short_id(ip.get('host_id'))}")


def print_tags(data: list[dict] | dict, as_json: bool = False) -> None:
    """Print tags table."""
    items = data if isinstance(data, list) else data.get("data", [])
    if as_json:
        print_json(data)
        return
    if HAS_RICH:
        t = Table(title=f"Tags ({len(items)})")
        t.add_column("ID", style="cyan", no_wrap=True, max_width=36)
        t.add_column("Name", style="bold")
        t.add_column("Color")
        for tag in items:
            t.add_row(
                str(tag.get("id", "")),
                tag.get("name") or "—",
                tag.get("color") or "—",
            )
        console.print(t)
    else:
        for tag in items:
            print(f"  {tag.get('id')}  {tag.get('name') or '—'}")


def print_vlans(data: list[dict] | dict, as_json: bool = False) -> None:
    """Print VLANs table."""
    items = data if isinstance(data, list) else data.get("data", [])
    if as_json:
        print_json(data)
        return
    if HAS_RICH:
        t = Table(title=f"VLANs ({len(items)})")
        t.add_column("ID", style="cyan", no_wrap=True, max_width=36)
        t.add_column("Name", style="bold")
        t.add_column("VID", justify="right")
        t.add_column("Network")
        for v in items:
            t.add_row(
                str(v.get("id", "")),
                v.get("name") or "—",
                str(v.get("vid") or v.get("vlan_id") or "—"),
                _short_id(v.get("network_id")),
            )
        console.print(t)
    else:
        for v in items:
            print(f"  {v.get('id')}  {v.get('name') or '—'}  vid={v.get('vid', '—')}")


def print_users(data: list[dict] | dict, as_json: bool = False) -> None:
    """Print users table."""
    items = data if isinstance(data, list) else data.get("data", [])
    if as_json:
        print_json(data)
        return
    if HAS_RICH:
        t = Table(title=f"Users ({len(items)})")
        t.add_column("ID", style="cyan", no_wrap=True, max_width=36)
        t.add_column("Username", style="bold")
        t.add_column("Email")
        t.add_column("Role")
        for u in items:
            t.add_row(
                str(u.get("id", "")),
                u.get("username") or u.get("name") or "—",
                u.get("email") or "—",
                u.get("role") or "—",
            )
        console.print(t)
    else:
        for u in items:
            print(f"  {u.get('id')}  {u.get('username') or u.get('name', '—')}")


def print_topology_list(data: list[dict] | dict, as_json: bool = False) -> None:
    """Print topology list."""
    items = data if isinstance(data, list) else data.get("data", [])
    if as_json:
        print_json(data)
        return
    if HAS_RICH:
        t = Table(title=f"Topologies ({len(items)})")
        t.add_column("ID", style="cyan", no_wrap=True, max_width=36)
        t.add_column("Name", style="bold")
        t.add_column("Network")
        t.add_column("Views", justify="right")
        for topo in items:
            t.add_row(
                str(topo.get("id", "")),
                topo.get("name") or "—",
                _short_id(topo.get("network_id")),
                str(len(topo.get("views") or topo.get("available_views") or [])),
            )
        console.print(t)
    else:
        for topo in items:
            print(f"  {topo.get('id')}  {topo.get('name') or '—'}")


def print_topology_data(data: dict, as_json: bool = False) -> None:
    """Print topology data summary."""
    if as_json:
        print_json(data)
        return
    payload = data.get("data", data) if isinstance(data, dict) else data
    nodes_by_view = payload.get("nodes", {})
    edges_by_view = payload.get("edges", {})
    views = payload.get("available_views") or list(nodes_by_view.keys()) if isinstance(nodes_by_view, dict) else []
    hosts = payload.get("hosts", [])
    subnets = payload.get("subnets", [])

    if HAS_RICH:
        console.print("[bold cyan]Topology Data[/]")
        console.print(f"  Hosts   : {len(hosts)}")
        console.print(f"  Subnets : {len(subnets)}")
        if views:
            console.print(f"  Views   : {', '.join(str(v) for v in views)}")
        if isinstance(nodes_by_view, dict):
            for vname, vnode in nodes_by_view.items():
                vedge = edges_by_view.get(vname, []) if isinstance(edges_by_view, dict) else []
                containers = sum(1 for n in vnode if (n.get("node_type") or "").lower() == "container")
                elements = sum(1 for n in vnode if (n.get("node_type") or "").lower() == "element")
                console.print(f"  [{vname}] Nodes: {len(vnode)} ({containers} containers, {elements} elements), Edges: {len(vedge)}")
        else:
            console.print(f"  Nodes   : {len(nodes_by_view)}")
            console.print(f"  Edges   : {len(edges_by_view)}")
    else:
        print(f"Hosts: {len(hosts)}, Subnets: {len(subnets)}, Views: {views}")


def print_mermaid(text: str) -> None:
    """Print Mermaid diagram text."""
    print(text)
