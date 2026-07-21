---
name: scanopy-cli
description: CLI client for the Scanopy network discovery API — hosts, services, ports, IPs, subnets, VLANs, topology, and Mermaid export
---

# scanopy-cli (`sc`)

CLI for the Scanopy network discovery & mapping service.

## Quick Reference

| Command | Endpoint | Description |
|---------|----------|-------------|
| `sc ping` | `GET /api/health` | Check server connectivity |
| `sc info` | `GET /api/health` | Server version & status |
| `sc config` | `GET /api/config` | Public server config |
| `sc hosts` | `GET /api/hosts` | List all hosts |
| `sc host <id>` | `GET /api/v1/hosts/{id}` | Single host detail |
| `sc services` | `GET /api/services` | List all services |
| `sc search <q>` | (client-side) | Search hosts+services by name/IP/MAC |
| `sc networks` | `GET /api/v1/networks` | List networks |
| `sc subnets` | `GET /api/v1/subnets` | List subnets (CIDR, VLAN) |
| `sc ports` | `GET /api/v1/ports` | List all ports |
| `sc ips` | `GET /api/v1/ip-addresses` | List all IP addresses |
| `sc tags` | `GET /api/v1/tags` | List tags |
| `sc vlans` | `GET /api/v1/vlans` | List VLANs |
| `sc users` | `GET /api/v1/users` | List users |
| `sc org` | `GET /api/v1/organizations` | Organization info |
| `sc topology` | `GET /api/v1/topology` | List topologies |
| `sc topology-data -i <net>` | `GET /api/v1/topology/data?network_id=X` | Full topology data |
| `sc topology-export -i <net> -f mermaid` | (same + transform) | Export as Mermaid .mmd |
| `sc topology-export -i <net> -f json` | (same) | Export raw JSON |

## Global Options

All commands accept: `--json/-j` (raw JSON), `--url/-u`, `--api-key/-k`, `--timeout/-t`.

## Common Workflows

**Find all open ports:**
```bash
sc ports --json | jq '.[] | select(.type == "open")'
```

**List Docker containers:**
```bash
sc search docker
```

**Export topology as Mermaid:**
```bash
sc topology-export -i <network-id> -f mermaid -o network.mmd
```

**Search by IP:**
```bash
sc search 192.168.1.10
```

**Get host details:**
```bash
sc host <host-uuid>
```

## Auth

Set `SCANOPY_API_KEY` env var or pass `--api-key`. Uses Bearer token auth.

## Response Format

All API responses: `{"success": bool, "data": ..., "error": ..., "meta": {...}}`.
Pagination: `meta.pagination` → `total_count`, `limit`, `offset`, `has_more`.
