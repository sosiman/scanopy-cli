"""CLI entry point for Scanopy."""

from __future__ import annotations
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import click
from . import __version__
from .client import ServiceClient, ServiceError
from .formatters import (
    console,
    print_health,
    print_host_detail,
    print_hosts,
    print_json,
    print_search_results,
    print_services,
    print_networks,
    print_subnets,
    print_ports,
    print_ips,
    print_tags,
    print_vlans,
    print_users,
    print_topology_list,
    print_topology_data,
    print_mermaid,
)


def _handle_error(exc: ServiceError) -> None:
    msg = f"Error: {exc}"
    if console:
        console.print(f"[bold red]{msg}[/]")
    else:
        print(msg, file=sys.stderr)
    sys.exit(1)


# ── root group ───────────────────────────────────────────────────────


@click.group()
@click.version_option(version=__version__, prog_name="sc")
@click.option(
    "--url",
    "-u",
    envvar="SCANOPY_URL",
    default="http://localhost:60072",
    show_default=True,
    help="Scanopy API base URL.",
)
@click.option(
    "--api-key",
    "-k",
    envvar="SCANOPY_API_KEY",
    default="",
    help="API key (Bearer token).",
)
@click.option(
    "--timeout",
    "-t",
    default=10,
    show_default=True,
    help="Request timeout in seconds.",
)
@click.option(
    "--json",
    "-j",
    "as_json",
    is_flag=True,
    help="Output raw JSON.",
)
@click.pass_context
def cli(ctx: click.Context, url: str, api_key: str, timeout: int, as_json: bool) -> None:
    """Scanopy CLI — command-line interface for the Scanopy API."""
    ctx.ensure_object(dict)
    ctx.obj["client"] = ServiceClient(base_url=url, api_key=api_key, timeout=timeout)
    ctx.obj["as_json"] = as_json


# ── info ─────────────────────────────────────────────────────────────


@cli.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Show server version and status."""
    try:
        data = ctx.obj["client"].info()
        print_health(data, as_json=ctx.obj["as_json"])
    except ServiceError as exc:
        _handle_error(exc)


# ── ping ─────────────────────────────────────────────────────────────


@cli.command()
@click.pass_context
def ping(ctx: click.Context) -> None:
    """Check connectivity to the Scanopy server."""
    try:
        ok = ctx.obj["client"].ping()
        if ok:
            msg = "pong — Scanopy server is reachable"
            if console:
                console.print(f"[green]{msg}[/]")
            else:
                print(msg)
        else:
            msg = "Scanopy server did not respond with a healthy status"
            if console:
                console.print(f"[yellow]{msg}[/]")
            else:
                print(msg)
            sys.exit(1)
    except ServiceError as exc:
        _handle_error(exc)


# ── config ───────────────────────────────────────────────────────────


@cli.command()
@click.pass_context
def config(ctx: click.Context) -> None:
    """Show public server configuration."""
    try:
        envelope = ctx.obj["client"].config()
        data = envelope.get("data", envelope)
        if ctx.obj["as_json"]:
            print_json(envelope)
        else:
            if console:
                console.print("[bold cyan]Server Configuration[/]")
                if isinstance(data, dict):
                    for k, v in data.items():
                        console.print(f"  {k}: {v}")
                else:
                    console.print(data)
            else:
                print(data)
    except ServiceError as exc:
        _handle_error(exc)


# ── hosts ────────────────────────────────────────────────────────────


@cli.command()
@click.option("--limit", "-n", default=0, help="Max results (0 = all).")
@click.option("--offset", "-o", default=0, help="Skip first N results.")
@click.pass_context
def hosts(ctx: click.Context, limit: int, offset: int) -> None:
    """List all discovered hosts."""
    try:
        envelope = ctx.obj["client"].list_hosts(limit=limit, offset=offset)
        data = envelope.get("data", [])
        print_hosts(data, as_json=ctx.obj["as_json"])
    except ServiceError as exc:
        _handle_error(exc)


# ── host (single) ───────────────────────────────────────────────────


@cli.command()
@click.argument("host_id")
@click.pass_context
def host(ctx: click.Context, host_id: str) -> None:
    """Show detailed information for a single host."""
    try:
        envelope = ctx.obj["client"].get_host(host_id)
        print_host_detail(envelope["data"], as_json=ctx.obj["as_json"])
    except ServiceError as exc:
        _handle_error(exc)


# ── services ─────────────────────────────────────────────────────────


@cli.command()
@click.option("--limit", "-n", default=0, help="Max results (0 = all).")
@click.option("--offset", "-o", default=0, help="Skip first N results.")
@click.pass_context
def services(ctx: click.Context, limit: int, offset: int) -> None:
    """List all discovered services."""
    try:
        envelope = ctx.obj["client"].list_services(limit=limit, offset=offset)
        data = envelope.get("data", [])
        print_services(data, as_json=ctx.obj["as_json"])
    except ServiceError as exc:
        _handle_error(exc)


# ── search ───────────────────────────────────────────────────────────


@cli.command()
@click.argument("query")
@click.pass_context
def search(ctx: click.Context, query: str) -> None:
    """Search hosts and services by name, IP, or MAC."""
    try:
        results = ctx.obj["client"].search(query)
        print_search_results(results, as_json=ctx.obj["as_json"])
    except ServiceError as exc:
        _handle_error(exc)


# ── networks ─────────────────────────────────────────────────────────


@cli.command()
@click.pass_context
def networks(ctx: click.Context) -> None:
    """List all networks."""
    try:
        envelope = ctx.obj["client"].list_networks()
        data = envelope.get("data", [])
        print_networks(data, as_json=ctx.obj["as_json"])
    except ServiceError as exc:
        _handle_error(exc)


# ── subnets ──────────────────────────────────────────────────────────


@cli.command()
@click.option("--limit", "-n", default=0, help="Max results (0 = all).")
@click.option("--offset", "-o", default=0, help="Skip first N results.")
@click.pass_context
def subnets(ctx: click.Context, limit: int, offset: int) -> None:
    """List all subnets."""
    try:
        envelope = ctx.obj["client"].list_subnets(limit=limit, offset=offset)
        data = envelope.get("data", [])
        print_subnets(data, as_json=ctx.obj["as_json"])
    except ServiceError as exc:
        _handle_error(exc)


# ── ports ────────────────────────────────────────────────────────────


@cli.command()
@click.option("--limit", "-n", default=0, help="Max results (0 = all).")
@click.option("--offset", "-o", default=0, help="Skip first N results.")
@click.pass_context
def ports(ctx: click.Context, limit: int, offset: int) -> None:
    """List all ports."""
    try:
        envelope = ctx.obj["client"].list_ports(limit=limit, offset=offset)
        data = envelope.get("data", [])
        print_ports(data, as_json=ctx.obj["as_json"])
    except ServiceError as exc:
        _handle_error(exc)


# ── ips ──────────────────────────────────────────────────────────────


@cli.command("ips")
@click.option("--limit", "-n", default=0, help="Max results (0 = all).")
@click.option("--offset", "-o", default=0, help="Skip first N results.")
@click.pass_context
def ips_cmd(ctx: click.Context, limit: int, offset: int) -> None:
    """List all IP addresses."""
    try:
        envelope = ctx.obj["client"].list_ip_addresses(limit=limit, offset=offset)
        data = envelope.get("data", [])
        print_ips(data, as_json=ctx.obj["as_json"])
    except ServiceError as exc:
        _handle_error(exc)


# ── tags ─────────────────────────────────────────────────────────────


@cli.command()
@click.pass_context
def tags(ctx: click.Context) -> None:
    """List all tags."""
    try:
        envelope = ctx.obj["client"].list_tags()
        data = envelope.get("data", [])
        print_tags(data, as_json=ctx.obj["as_json"])
    except ServiceError as exc:
        _handle_error(exc)


# ── vlans ────────────────────────────────────────────────────────────


@cli.command()
@click.pass_context
def vlans(ctx: click.Context) -> None:
    """List all VLANs."""
    try:
        envelope = ctx.obj["client"].list_vlans()
        data = envelope.get("data", [])
        print_vlans(data, as_json=ctx.obj["as_json"])
    except ServiceError as exc:
        _handle_error(exc)


# ── users ────────────────────────────────────────────────────────────


@cli.command()
@click.pass_context
def users(ctx: click.Context) -> None:
    """List all users."""
    try:
        envelope = ctx.obj["client"].list_users()
        data = envelope.get("data", [])
        print_users(data, as_json=ctx.obj["as_json"])
    except ServiceError as exc:
        _handle_error(exc)


# ── org ──────────────────────────────────────────────────────────────


@cli.command("org")
@click.pass_context
def org_cmd(ctx: click.Context) -> None:
    """Show organization info."""
    try:
        envelope = ctx.obj["client"].get_organization()
        data = envelope.get("data", envelope)
        if ctx.obj["as_json"]:
            print_json(envelope)
        else:
            if console:
                console.print("[bold cyan]Organization[/]")
                if isinstance(data, dict):
                    for k, v in data.items():
                        console.print(f"  {k}: {v}")
                else:
                    console.print(data)
            else:
                print(data)
    except ServiceError as exc:
        _handle_error(exc)


# ── topology ─────────────────────────────────────────────────────────


@cli.command()
@click.pass_context
def topology(ctx: click.Context) -> None:
    """List all topologies."""
    try:
        envelope = ctx.obj["client"].topology_list()
        data = envelope.get("data", [])
        print_topology_list(data, as_json=ctx.obj["as_json"])
    except ServiceError as exc:
        _handle_error(exc)


# ── topology-data ────────────────────────────────────────────────────


@cli.command("topology-data")
@click.option("--network-id", "-i", required=True, help="Network ID.")
@click.pass_context
def topology_data_cmd(ctx: click.Context, network_id: str) -> None:
    """Show full topology data for a network."""
    try:
        envelope = ctx.obj["client"].topology_data(network_id)
        if ctx.obj["as_json"]:
            print_json(envelope)
        else:
            print_topology_data(envelope)
    except ServiceError as exc:
        _handle_error(exc)


# ── topology-export ──────────────────────────────────────────────────

def _build_mermaid(topo_data: dict, view: str = "L3Logical") -> str:
    """Build a Mermaid flowchart from topology nodes/edges for a given view.

    The API returns nodes/edges as dicts keyed by view name, e.g.:
      {"nodes": {"L3Logical": [...], "Workloads": [...]}, "edges": {"L3Logical": [...], ...}}
    """
    payload = topo_data.get("data", topo_data) if isinstance(topo_data, dict) else topo_data
    nodes_by_view = payload.get("nodes", {})
    edges_by_view = payload.get("edges", {})

    # Resolve the requested view — prefer the explicit view, else first non-empty
    if isinstance(nodes_by_view, dict):
        available_views = list(nodes_by_view.keys())
        if view and view in nodes_by_view:
            nodes = nodes_by_view[view]
        else:
            # Pick first view that actually has nodes
            chosen = next((v for v in available_views if nodes_by_view[v]), available_views[0] if available_views else "")
            view = chosen
            nodes = nodes_by_view.get(view, [])
    else:
        nodes = nodes_by_view

    if isinstance(edges_by_view, dict):
        edges = edges_by_view.get(view, [])
    else:
        edges = edges_by_view

    # Sanitize IDs for Mermaid (replace dashes etc.)
    def safe_id(s: str) -> str:
        return s.replace("-", "_").replace(" ", "_").replace(".", "_").replace("@", "_")

    lines = ["flowchart TD"]

    # Separate containers and elements
    containers = [n for n in nodes if (n.get("node_type") or "").lower() == "container"]
    elements = [n for n in nodes if (n.get("node_type") or "").lower() == "element"]

    container_ids = {str(c.get("id", "")) for c in containers}

    # Build child map: container_id -> [elements]
    child_map: dict[str, list[dict]] = {}
    orphan_elements = []
    for e in elements:
        cid = str(e.get("container_id") or "")
        if cid and cid in container_ids:
            child_map.setdefault(cid, []).append(e)
        else:
            orphan_elements.append(e)

    # Emit subgraphs for containers
    for c in containers:
        cid = str(c.get("id", ""))
        label = c.get("header") or c.get("label") or c.get("name") or cid
        # Truncate very long labels for readability
        if len(label) > 80:
            label = label[:77] + "..."
        lines.append(f"    subgraph {safe_id(cid)}[\"{label}\"]")
        children = child_map.get(cid, [])
        if children:
            for ch in children:
                chid = str(ch.get("id", ""))
                chlabel = ch.get("header") or ch.get("label") or ch.get("name") or chid[:12]
                if len(chlabel) > 60:
                    chlabel = chlabel[:57] + "..."
                lines.append(f"        {safe_id(chid)}[\"{chlabel}\"]")
        else:
            lines.append(f"        {safe_id(cid)}_ph[\"...\"]")
        lines.append("    end")

    # Emit orphan elements
    for e in orphan_elements:
        eid = str(e.get("id", ""))
        elabel = e.get("header") or e.get("label") or e.get("name") or eid[:12]
        if len(elabel) > 60:
            elabel = elabel[:57] + "..."
        lines.append(f"    {safe_id(eid)}[\"{elabel}\"]")

    # Emit edges
    for edge in edges:
        src = str(edge.get("source") or edge.get("source_id") or "")
        tgt = str(edge.get("target") or edge.get("target_id") or "")
        label = edge.get("label") or ""
        if src and tgt:
            if label:
                # Escape quotes in label
                label = label.replace('"', "'")
                lines.append(f"    {safe_id(src)} -->|\"{label}\"| {safe_id(tgt)}")
            else:
                lines.append(f"    {safe_id(src)} --> {safe_id(tgt)}")

    return "\n".join(lines)


@cli.command("topology-export")
@click.option("--network-id", "-i", required=True, help="Network ID.")
@click.option("--view", "-v", default="", help="View name (e.g. L3Logical).")
@click.option("--format", "-f", "fmt", type=click.Choice(["mermaid", "json", "png", "svg", "pdf", "html"]), default="mermaid", help="Export format.")
@click.option("--output", "-o", "outfile", default="", help="Output file path (default: stdout for mermaid/json).")
@click.option("--width", default=1920, help="Image width for png/svg (default: 1920).")
@click.option("--height", default=1080, help="Image height for png/svg (default: 1080).")
@click.option("--bg", default="white", help="Background color for png/svg/pdf (default: white).")
@click.pass_context
def topology_export_cmd(ctx: click.Context, network_id: str, view: str, fmt: str, outfile: str, width: int, height: int, bg: str) -> None:
    """Export topology as Mermaid, JSON, PNG, SVG, PDF, or HTML.

    Visual formats (png/svg/pdf/html) require mermaid-cli: npm i -g @mermaid-js/mermaid-cli

    \b
    Examples:
      sc topology-export -i NET_ID --format mermaid
      sc topology-export -i NET_ID --format png -o network.png
      sc topology-export -i NET_ID --format pdf -o network.pdf --bg white
      sc topology-export -i NET_ID --format html -o network.html
    """
    try:
        envelope = ctx.obj["client"].topology_data(network_id)
        payload = envelope.get("data", envelope) if isinstance(envelope, dict) else envelope

        if fmt == "json":
            output = json.dumps(envelope, indent=2, default=str)
            if outfile:
                Path(outfile).write_text(output)
                _print_success(f"Exported to {outfile}")
            else:
                print(output)
            return

        # Generate Mermaid content
        if view and isinstance(payload, dict):
            available = payload.get("available_views") or payload.get("views") or []
            if view not in [str(v) for v in available] and available:
                if console:
                    console.print(f"[yellow]Warning: view '{view}' not in available views: {available}[/]")

        mermaid_content = _build_mermaid(envelope, view=view)

        if fmt == "mermaid":
            if outfile:
                Path(outfile).write_text(mermaid_content)
                _print_success(f"Exported to {outfile}")
            else:
                print(mermaid_content)
            return

        # Visual formats — need mmdc
        _render_visual(mermaid_content, fmt, outfile, width, height, bg)

    except ServiceError as exc:
        _handle_error(exc)


def _print_success(msg: str) -> None:
    if console:
        console.print(f"[green]{msg}[/]")
    else:
        print(msg)


def _mermaid_to_html(mermaid_content: str) -> str:
    """Generate a standalone HTML page with embedded Mermaid.js diagram."""
    import html as html_mod
    escaped = html_mod.escape(mermaid_content)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Scanopy Network Topology</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         margin: 0; padding: 20px; background: #f5f5f5; }}
  .container {{ max-width: 1400px; margin: 0 auto; background: white;
                border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 30px; }}
  h1 {{ color: #333; margin-bottom: 5px; }}
  .meta {{ color: #888; font-size: 14px; margin-bottom: 20px; }}
  .mermaid {{ display: flex; justify-content: center; }}
  .export-info {{ margin-top: 20px; padding: 15px; background: #f0f7ff;
                  border-radius: 6px; font-size: 13px; color: #555; }}
</style>
</head>
<body>
<div class="container">
  <h1>🌐 Scanopy Network Topology</h1>
  <p class="meta">Generated by scanopy-cli • {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
  <div class="mermaid">
{escaped}
  </div>
  <div class="export-info">
    <strong>Tip:</strong> Use browser Print (Ctrl+P) to save as PDF, or right-click the diagram to save as PNG/SVG.
  </div>
</div>
<script>mermaid.initialize({{ startOnLoad: true, theme: 'default', flowchart: {{ useMaxWidth: true }} }});</script>
</body>
</html>"""


def _render_visual(mermaid_content: str, fmt: str, outfile: str, width: int, height: int, bg: str) -> None:
    """Render Mermaid content to png/svg/pdf/html using mmdc."""
    mmdc = shutil.which("mmdc")
    if not mmdc:
        msg = "mermaid-cli (mmdc) not found. Install with: npm i -g @mermaid-js/mermaid-cli"
        if console:
            console.print(f"[red]Error: {msg}[/]")
        else:
            print(f"Error: {msg}", file=sys.stderr)
        sys.exit(1)

    # Default output filename
    if not outfile:
        outfile = f"topology.{fmt}"

    # Create temp .mmd file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as f:
        f.write(mermaid_content)
        mmd_path = f.name

    # Puppeteer config for running as root (servers)
    puppeteer_cfg = Path("/tmp/scanopy-puppeteer.json")
    if not puppeteer_cfg.exists():
        puppeteer_cfg.write_text('{"args": ["--no-sandbox", "--disable-setuid-sandbox"]}')

    try:
        # Build mmdc command
        cmd = [mmdc, "-i", mmd_path, "-o", outfile, "-b", bg, "-p", str(puppeteer_cfg)]

        if fmt in ("png", "svg", "pdf"):
            cmd.extend(["-w", str(width), "-H", str(height)])

        if fmt == "html":
            # Generate standalone HTML with embedded Mermaid.js
            html_content = _mermaid_to_html(mermaid_content)
            Path(outfile).write_text(html_content)
            size = Path(outfile).stat().st_size
            _print_success(f"Exported to {outfile} ({size:,} bytes)")
            return

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            stderr = result.stderr.strip()
            if console:
                console.print(f"[red]mmdc error: {stderr}[/]")
            else:
                print(f"mmdc error: {stderr}", file=sys.stderr)
            sys.exit(1)

        size = Path(outfile).stat().st_size if Path(outfile).exists() else 0
        _print_success(f"Exported to {outfile} ({size:,} bytes)")

    finally:
        Path(mmd_path).unlink(missing_ok=True)


# ── entry point ──────────────────────────────────────────────────────


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
