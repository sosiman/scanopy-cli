"""Render topology to PNG/SVG/PDF using vis.js + Playwright headless."""

from __future__ import annotations

import base64
import json
import shutil
import sys
from pathlib import Path


def render_topology_png(
    topology_data: dict,
    output_path: str,
    view: str = "L3Logical",
    width: int = 2400,
    height: int = 1600,
) -> str:
    """Render topology data to PNG using vis.js in headless Chromium."""
    from playwright.sync_api import sync_playwright

    nodes, edges = _extract_elements(topology_data, view)
    vis_data = json.dumps({"nodes": nodes, "edges": edges})
    html = _build_html(vis_data, width, height)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": width, "height": height})
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(4000)

        # Extract from canvas
        data_url = page.evaluate("() => document.querySelector('canvas')?.toDataURL('image/png')")
        if data_url and data_url.startswith("data:image"):
            b64 = data_url.split(",")[1]
            Path(output_path).write_bytes(base64.b64decode(b64))
        else:
            page.screenshot(path=output_path, full_page=True)

        browser.close()

    size = Path(output_path).stat().st_size
    return f"Exported to {output_path} ({size:,} bytes)"


def render_topology_pdf(
    topology_data: dict,
    output_path: str,
    view: str = "L3Logical",
    width: int = 2400,
    height: int = 1600,
) -> str:
    """Render topology data to PDF."""
    from playwright.sync_api import sync_playwright

    nodes, edges = _extract_elements(topology_data, view)
    vis_data = json.dumps({"nodes": nodes, "edges": edges})
    html = _build_html(vis_data, width, height)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": width, "height": height})
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(4000)
        page.pdf(path=output_path, format="A3", landscape=True, print_background=True)
        browser.close()

    size = Path(output_path).stat().st_size
    return f"Exported to {output_path} ({size:,} bytes)"


def render_topology_html(
    topology_data: dict,
    output_path: str,
    view: str = "L3Logical",
) -> str:
    """Generate standalone HTML with vis.js topology."""
    nodes, edges = _extract_elements(topology_data, view)
    vis_data = json.dumps({"nodes": nodes, "edges": edges})
    html = _build_html_standalone(vis_data)
    Path(output_path).write_text(html)
    size = Path(output_path).stat().st_size
    return f"Exported to {output_path} ({size:,} bytes)"


def _extract_elements(topology_data: dict, view: str) -> tuple[list, list]:
    """Extract vis.js nodes and edges from topology API response."""
    payload = topology_data.get("data", topology_data) if isinstance(topology_data, dict) else topology_data
    nodes_by_view = payload.get("nodes", {})
    edges_by_view = payload.get("edges", {})

    if isinstance(nodes_by_view, dict):
        if view in nodes_by_view:
            raw_nodes = nodes_by_view[view]
        else:
            raw_nodes = next((v for v in nodes_by_view.values() if v), [])
    else:
        raw_nodes = nodes_by_view

    if isinstance(edges_by_view, dict):
        raw_edges = edges_by_view.get(view, [])
    else:
        raw_edges = edges_by_view

    vis_nodes = []
    for n in raw_nodes:
        nid = n["id"]
        if n.get("node_type") == "Container":
            label = (n.get("header") or nid)[:60]
            vis_nodes.append({
                "id": nid, "label": label, "shape": "box",
                "color": {"background": "#E8EAF6", "border": "#3F51B5"},
                "font": {"size": 14, "bold": True, "color": "#283593"},
                "margin": 10, "widthConstraint": {"maximum": 200},
            })
        else:
            label = (n.get("header") or n.get("label") or nid[:12])[:40]
            parent = n.get("container_id", "")
            node = {
                "id": nid, "label": label, "shape": "box",
                "color": {"background": "#E8F5E9", "border": "#43A047"},
                "font": {"size": 11, "color": "#1B5E20"},
                "margin": 6, "widthConstraint": {"maximum": 180},
            }
            if parent:
                node["group"] = parent
            vis_nodes.append(node)

    vis_edges = []
    for e in raw_edges:
        src = e.get("source", "")
        tgt = e.get("target", "")
        label = (e.get("label") or "")[:25]
        if src and tgt:
            vis_edges.append({
                "from": src, "to": tgt, "label": label,
                "font": {"size": 9}, "color": {"color": "#78909C"},
            })

    return vis_nodes, vis_edges


def _build_html(vis_data: str, width: int, height: int) -> str:
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>body{{margin:0;background:#fff}}#net{{width:{width}px;height:{height}px}}</style>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
</head><body><div id="net"></div>
<script>
var data={vis_data};
new vis.Network(document.getElementById('net'),data,{{
  layout:{{hierarchical:{{enabled:true,direction:'UD',sortMethod:'hubsize',levelSeparation:100,nodeSpacing:80}}}},
  physics:{{enabled:false}},
  edges:{{smooth:{{type:'cubicBezier'}}}}
}});
</script></body></html>"""


def _build_html_standalone(vis_data: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Scanopy Network Topology</title>
<style>
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;margin:0;padding:20px;background:#f5f5f5}}
  .container{{max-width:1600px;margin:0 auto;background:#fff;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,.1);padding:30px}}
  h1{{color:#333;margin-bottom:5px}}
  .meta{{color:#888;font-size:14px;margin-bottom:20px}}
  #net{{width:100%;height:80vh;border:1px solid #e0e0e0;border-radius:4px}}
</style>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
</head><body>
<div class="container">
  <h1>🌐 Scanopy Network Topology</h1>
  <p class="meta">Generated by scanopy-cli</p>
  <div id="net"></div>
</div>
<script>
var data={vis_data};
new vis.Network(document.getElementById('net'),data,{{
  layout:{{hierarchical:{{enabled:true,direction:'UD',sortMethod:'hubsize',levelSeparation:100,nodeSpacing:80}}}},
  physics:{{enabled:false}},
  edges:{{smooth:{{type:'cubicBezier'}}}}
}});
</script></body></html>"""
