"""Split an IKEA web 3D model (GLB) into its physical parts.

IKEA's web models are usually one merged mesh. Pieces that are not connected to each other
(a leg, a bolt, a screw) are still separate in the geometry, so this script:
  1. decodes the GLB (including Draco compression),
  2. finds every connected piece (triangles sharing vertex positions, welded at 0.1 mm),
  3. names each piece from its shape and position (leg, rail, panel, bolt/screw ...),
  4. writes a new GLB: one node per part, grouped, with each part's pivot at its centre,
  5. writes a parts.json report you can edit to rename parts and re-run.

Usage
  python split_parts.py model.glb                       -> model_parts.glb + model_parts.json
  python split_parts.py model.glb -o out.glb --names names.json
  python split_parts.py model.glb --weld 0.5 --min-tris 4

names.json (optional) renames parts by their automatic name or id:
  { "Panel horizontal": {"name": "Seat", "group": "Seat"},
    "P07": {"name": "Back bow", "group": "Backrest"} }

Conventions: glTF meters, +Y up, +Z = front. "left/right" = as seen from the front.
Requires: numpy, scipy, pygltflib, DracoPy  (pip install numpy scipy pygltflib DracoPy)
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from ikea_glb import Prim, TreeNode, apply, read_glb, write_glb

GROUP_ORDER = ["Panel", "Body", "Leg", "Post", "Rail", "Hardware", "Other"]


# ---------------------------------------------------------------------------- 1. pieces
def find_pieces(pos: np.ndarray, tris: np.ndarray, weld_m: float) -> np.ndarray:
    """Label each triangle with the id of the connected piece it belongs to."""
    key = np.round(pos / weld_m).astype(np.int64)
    _, vid = np.unique(key, axis=0, return_inverse=True)       # welded vertex id
    vid = vid.ravel()
    t = vid[tris]                                              # (m, 3) welded ids
    n = vid.max() + 1
    rows = np.concatenate([t[:, 0], t[:, 1], t[:, 2]])
    cols = np.concatenate([t[:, 1], t[:, 2], t[:, 0]])
    graph = coo_matrix((np.ones(len(rows), np.int8), (rows, cols)), shape=(n, n))
    _, vlabel = connected_components(graph, directed=False)
    return vlabel[t[:, 0]]


# ---------------------------------------------------------------------------- 2. names
def classify(pts: np.ndarray, floor_y: float) -> tuple[str, str]:
    """Return (kind, group) from the piece's shape. Dimensions in cm."""
    size = (pts.max(0) - pts.min(0)) * 100
    # principal axes give true length/thickness even for tilted parts (spindles, splayed legs)
    c = pts - pts.mean(0)
    _, _, vt = np.linalg.svd(c, full_matrices=False) if len(pts) >= 3 else (None, None, np.eye(3))
    ext = np.sort(np.ptp(c @ vt.T, axis=0) * 100)[::-1]          # a >= b >= c
    a, b, cc = ext
    vertical = abs(vt[0][1]) > 0.7                              # main axis points up
    on_floor = (pts[:, 1].min() - floor_y) * 100 < 1.0
    if a < 6:
        if a / max(b, 1e-6) >= 2.5:
            return "Bolt/screw", "Hardware"
        if cc / a < 0.45:
            return "Screw head/washer", "Hardware"
        return "Nut/fitting", "Hardware"
    if on_floor and vertical and a / max(b, 1e-6) >= 2.5:
        return "Leg", "Leg"
    if a / max(b, 1e-6) >= 4:
        return ("Post", "Post") if vertical else ("Rail", "Rail")
    if cc / max(b, 1e-6) < 0.2:
        horizontal = size[1] <= min(size[0], size[2])
        return ("Panel horizontal", "Panel") if horizontal else ("Panel vertical", "Panel")
    return "Body", "Body"


def position_words(center: np.ndarray, mid: np.ndarray, extent: np.ndarray) -> str:
    words = []
    dz, dx = center[2] - mid[2], center[0] - mid[0]
    if abs(dz) > 0.08 * extent[2]:
        words.append("front" if dz > 0 else "back")
    if abs(dx) > 0.08 * extent[0]:
        words.append("left" if dx < 0 else "right")
    return " ".join(words)


# ---------------------------------------------------------------------------- reusable steps
def analyze(model, weld_mm: float = 0.1, min_tris: int = 1, names: dict | None = None) -> list[dict]:
    """Find, classify and name every separate piece. Returns piece dicts (sorted, with ids)."""
    pieces = []
    for node, world in model.mesh_nodes():
        for prim in node.prims:
            pos_w = apply(world, prim.attributes["POSITION"])
            labels = find_pieces(pos_w, prim.indices, weld_mm / 1000)
            for lab in np.unique(labels):
                tris = prim.indices[labels == lab]
                if len(tris) >= min_tris:
                    pieces.append(dict(prim=prim, world=world, tris=tris, pts=pos_w[np.unique(tris)]))
    allpts = np.concatenate([p["pts"] for p in pieces])
    lo, hi = allpts.min(0), allpts.max(0)
    mid, extent = (lo + hi) / 2, hi - lo
    for p in pieces:
        p["min"], p["max"] = p["pts"].min(0), p["pts"].max(0)
        p["center"] = (p["min"] + p["max"]) / 2
        p["kind"], p["group"] = classify(p["pts"], lo[1])
        where = position_words(p["center"], mid, extent) if p["group"] != "Hardware" else ""
        p["auto"] = f"{p['kind']} {where}".strip()
    # stable order: group, then size; then de-duplicate names with numbers
    pieces.sort(key=lambda p: (GROUP_ORDER.index(p["group"]), -len(p["tris"]), -p["center"][1], p["center"][0]))
    counts, seen = Counter(p["auto"] for p in pieces), Counter()
    for i, p in enumerate(pieces, 1):
        p["id"] = f"P{i:02d}"
        if counts[p["auto"]] > 1:
            seen[p["auto"]] += 1
            p["auto"] = f"{p['auto']} {seen[p['auto']]}"
        p["name"], p["final_group"] = p["auto"], p["group"]
    for p in pieces:
        r = (names or {}).get(p["id"]) or (names or {}).get(p["auto"])
        if r:
            p["name"] = r.get("name", p["name"])
            p["final_group"] = r.get("group", p["final_group"])
    return pieces


def piece_info(p: dict) -> dict:
    return {"part_id": p["id"], "part": p["name"], "group": p["final_group"], "auto_name": p["auto"],
            "triangles": int(len(p["tris"])), "size_cm": np.round((p["max"] - p["min"]) * 100, 1).tolist(),
            "center_cm": np.round(p["center"] * 100, 1).tolist()}


def build_tree(src_name: str, pieces: list[dict], weld_mm: float = 0.1) -> TreeNode:
    """root -> groups -> parts; each part's vertices are stored relative to its centre."""
    root = TreeNode(Path(src_name).stem, extras={"source": src_name, "split_by": "connected geometry", "weld_mm": weld_mm})
    groups: dict[str, TreeNode] = {}
    for p in pieces:
        prim, tris = p["prim"], p["tris"]
        used, inverse = np.unique(tris, return_inverse=True)
        attrs = {}
        for name, arr in prim.attributes.items():
            a = arr[used].copy()
            if name == "POSITION":
                a = apply(p["world"], a) - p["center"]
            elif name in ("NORMAL", "TANGENT"):
                v = a[:, :3] @ p["world"][:3, :3].T
                v /= np.linalg.norm(v, axis=1, keepdims=True) + 1e-12
                a = np.concatenate([v, a[:, 3:]], axis=1) if name == "TANGENT" else v
            attrs[name] = a
        node = TreeNode(p["name"], translation=p["center"].tolist(), extras=piece_info(p),
                        prims=[Prim(attrs, inverse.reshape(-1, 3).astype(np.uint32), prim.material)])
        g = p["final_group"]
        if g not in groups:
            groups[g] = TreeNode(f"{g} (group)", extras={"group": g})
            root.children.append(groups[g])
        groups[g].children.append(node)
    return root


# ---------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("glb")
    ap.add_argument("-o", "--out")
    ap.add_argument("--names", help="JSON file renaming parts (by auto name or id)")
    ap.add_argument("--weld", type=float, default=0.1, help="weld distance in mm (default 0.1)")
    ap.add_argument("--min-tris", type=int, default=1, help="drop pieces with fewer triangles")
    args = ap.parse_args()

    src = Path(args.glb)
    out_glb = Path(args.out) if args.out else src.with_name(src.stem + "_parts.glb")
    out_json = out_glb.with_suffix(".json")
    model = read_glb(str(src))
    names = json.loads(Path(args.names).read_text(encoding="utf-8")) if args.names else None
    pieces = analyze(model, args.weld, args.min_tris, names)
    print(f"{src.name}: {sum(len(n.prims) for n, _ in model.mesh_nodes())} mesh primitive(s) -> {len(pieces)} separate pieces")
    root = build_tree(src.name, pieces, args.weld)
    write_glb(str(out_glb), model, [root])
    report = [piece_info(p) for p in pieces]
    out_json.write_text(json.dumps({"source": src.name, "parts": report}, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"{'id':4} {'name':28} {'group':10} {'tris':>5}  size cm (W x H x D)")
    for r in report:
        s = r["size_cm"]
        print(f"{r['part_id']:4} {r['part'][:28]:28} {r['group']:10} {r['triangles']:5}  {s[0]} x {s[1]} x {s[2]}")
    print("\nGroups: " + ", ".join(f"{g.extras['group']} {len(g.children)}" for g in root.children))
    print(f"Wrote {out_glb} and {out_json}")


if __name__ == "__main__":
    main()
