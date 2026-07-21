# scanopy-cli

[![PyPI version](https://img.shields.io/pypi/v/scanopy-cli.svg)](https://pypi.org/project/scanopy-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**`sc`** — a fast, scriptable command-line interface for the [Scanopy](https://github.com/sosiman/scanopy) network scanner API.

## Install

```bash
pip install scanopy-cli
```

Or from source:

```bash
git clone https://github.com/sosiman/scanopy-cli.git
cd scanopy-cli
pip install -e .
```

## Quick Start

```bash
# Set your API key (or use --api-key / -k on every command)
export SCANOPY_API_KEY="scp_u_your_key_here"

# Check connectivity
sc ping

# Show server info
sc info

# List all hosts
sc hosts

# List all services
sc services

# Search by name, IP, or MAC
sc search 10.0.0
```

## Commands

| Command | Description |
|---|---|
| `sc info` | Show server version and status |
| `sc ping` | Check connectivity to the Scanopy server |
| `sc hosts` | List all discovered hosts |
| `sc host <id>` | Show detailed info for a single host |
| `sc services` | List all discovered services |
| `sc search <query>` | Search hosts and services by name, IP, or MAC |
| `sc --help` | Show help for all commands |
| `sc --version` | Show version |

## Global Options

| Option | Env Var | Description |
|---|---|---|
| `--url`, `-u` | `SCANOPY_URL` | API base URL (default: `http://localhost:60072`) |
| `--api-key`, `-k` | `SCANOPY_API_KEY` | Bearer token for authentication |
| `--timeout`, `-t` | — | Request timeout in seconds (default: `10`) |
| `--json`, `-j` | — | Output raw JSON (for scripting) |

## Examples

### List hosts as JSON

```bash
sc --json hosts | jq '.[] | {name, ip: .ip_addresses[0].ip}'
```

### Show host details

```bash
sc host 42
```

### Search across the network

```bash
sc search web-server
sc search 192.168.1
sc search AA:BB:CC
```

### Pipe-friendly JSON output

```bash
sc --json services | jq '.[] | select(.port == 443)'
```

### Use with a different server

```bash
sc --url https://scanopy.example.com --api-key scp_u_prod_key hosts
```

## Environment Variables

| Variable | Description |
|---|---|
| `SCANOPY_URL` | API base URL |
| `SCANOPY_API_KEY` | Bearer token (keys start with `scp_u_`) |

## Development

```bash
git clone https://github.com/sosiman/scanopy-cli.git
cd scanopy-cli
pip install -e ".[dev]"
pytest
```

## License

MIT © Sosi
