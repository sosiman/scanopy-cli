"""CLI entry point for Scanopy."""

from __future__ import annotations

import sys

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


# ── entry point ──────────────────────────────────────────────────────


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
