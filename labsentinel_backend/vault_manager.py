"""Vault Manager - Obsidian-compatible memory system for SENTINEL.

Reads and parses Markdown notes, frontmatter metadata, and [[wikilinks]]
from the Obsidian vault directory (/home/mauro/sentinel-vault).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

VAULT_DIR = Path(os.environ.get("SENTINEL_VAULT_DIR", str(Path.home() / "sentinel-vault")))

# Ensure base vault subdirectories exist
for sub in ["conceptos", "memoria", "laboratorio"]:
    try:
        (VAULT_DIR / sub).mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """Extract YAML-like frontmatter between --- and return (metadata, body)."""
    meta: Dict[str, Any] = {}
    if not content.startswith("---"):
        return meta, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return meta, content

    yaml_block = parts[1]
    body = parts[2].strip()

    for line in yaml_block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip().lower()
            val = val.strip()
            if val.startswith("[") and val.endswith("]"):
                meta[key] = [item.strip() for item in val[1:-1].split(",") if item.strip()]
            else:
                meta[key] = val.strip('"\'')
    return meta, body


def extract_wikilinks(text: str) -> List[str]:
    """Find all [[link_target]] or [[link_target|display_text]] in markdown."""
    pattern = r"\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]"
    matches = re.findall(pattern, text)
    return [m.strip() for m in matches if m.strip()]


def get_all_notes() -> List[Dict[str, Any]]:
    """Scan vault and return list of all parsed notes."""
    notes = []
    if not VAULT_DIR.exists():
        return notes

    for file_path in VAULT_DIR.rglob("*.md"):
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            meta, body = parse_frontmatter(content)
            wikilinks = extract_wikilinks(content)
            note_id = file_path.stem
            rel_path = file_path.relative_to(VAULT_DIR).as_posix()
            category = meta.get("categoria", file_path.parent.name if file_path.parent != VAULT_DIR else "general")
            title = meta.get("title", note_id.replace("_", " "))

            notes.append({
                "id": note_id,
                "title": title,
                "category": category,
                "tags": meta.get("tags", []),
                "links": wikilinks,
                "path": rel_path,
                "content": content,
                "body": body,
                "size": len(content),
                "modified": file_path.stat().st_mtime
            })
        except Exception:
            continue
    return notes


def build_graph() -> Dict[str, Any]:
    """Generate nodes and edges structure formatted for 2D/3D force graph visualization."""
    notes = get_all_notes()
    node_map = {n["id"].lower(): n for n in notes}

    nodes = []
    links = []

    # Category color mapping for visual excitement
    category_colors = {
        "conceptos": "#00f0ff",   # Bright Cyan
        "memoria": "#a855f7",     # Neural Purple
        "laboratorio": "#ffaa00", # Holographic Gold/Orange
        "general": "#22c55e",     # Matrix Emerald
    }

    for n in notes:
        cat = n["category"].lower()
        color = category_colors.get(cat, "#38bdf8")
        nodes.append({
            "id": n["id"],
            "name": n["title"],
            "group": n["category"],
            "val": max(12, min(36, 12 + len(n["links"]) * 4)),
            "color": color,
            "tags": n["tags"],
            "path": n["path"],
            "snippet": n["body"][:140] + ("..." if len(n["body"]) > 140 else "")
        })

    # Build unique directional or bidirectional edges
    seen_edges = set()
    for n in notes:
        src = n["id"]
        for target in n["links"]:
            # Check if target exists or is an external conceptual node
            edge_key = tuple(sorted([src.lower(), target.lower()]))
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                # If target doesn't exist yet as a file, auto-add as dynamic node!
                if target.lower() not in node_map:
                    nodes.append({
                        "id": target,
                        "name": target.replace("_", " "),
                        "group": "discovered",
                        "val": 10,
                        "color": "#64748b",
                        "tags": ["sin-definir"],
                        "path": "",
                        "snippet": "Concepto referenciado pendiente de documentar."
                    })
                    node_map[target.lower()] = {"id": target}

                links.append({
                    "source": src,
                    "target": target,
                    "value": 1
                })

    return {
        "nodes": nodes,
        "links": links,
        "total_nodes": len(nodes),
        "total_links": len(links),
        "vault_path": str(VAULT_DIR)
    }


def get_note_by_id(note_id: str) -> Optional[Dict[str, Any]]:
    """Fetch single note content and connections."""
    notes = get_all_notes()
    for n in notes:
        if n["id"].lower() == note_id.lower():
            # Find incoming links (backlinks)
            backlinks = [other["id"] for other in notes if any(link.lower() == note_id.lower() for link in other["links"])]
            n["backlinks"] = backlinks
            return n
    return None


def save_note(note_id: str, title: str, category: str, content: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create or update a note in the Obsidian vault."""
    clean_id = re.sub(r"[^\w\-_]", "_", note_id).strip("_")
    category = category.lower().strip() if category else "conceptos"
    target_dir = VAULT_DIR / category
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / f"{clean_id}.md"

    tags_str = f"[{', '.join(tags)}]" if tags else "[]"
    frontmatter = f"---\ntitle: {title}\ntags: {tags_str}\ncategoria: {category}\n---\n\n"
    
    if not content.startswith("---"):
        full_content = frontmatter + content.strip() + "\n"
    else:
        full_content = content.strip() + "\n"

    file_path.write_text(full_content, encoding="utf-8")
    return {
        "id": clean_id,
        "title": title,
        "path": file_path.relative_to(VAULT_DIR).as_posix(),
        "status": "saved"
    }


def search_notes(query: str) -> List[Dict[str, Any]]:
    """Simple semantic/keyword search across note titles and contents."""
    query = query.lower().strip()
    results = []
    for n in get_all_notes():
        score = 0
        if query in n["id"].lower():
            score += 10
        if query in n["title"].lower():
            score += 8
        if any(query in tag.lower() for tag in n["tags"]):
            score += 5
        if query in n["content"].lower():
            score += 2
        if score > 0:
            results.append({**n, "score": score})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
