"""Process a whole folder of IKEA web models into ONE catalog JSON.

For every .glb in the folder:
  - split into parts (split_parts.analyze) and describe each part (size, shape axes, hardware size),
  - find joints: which parts touch which, where, and how (fastener / end-in-socket / surface),
  - measure the overall size, and compare with a dimension spec if one is provided,
  - optionally join product info (title, category, price, materials) from the
    Hugging Face IKEA dataset (products-us.jsonl) by the 8-digit article number in the file name,
  - optionally save the split GLB for each product.
Then it builds cross-product indexes: identical hardware sizes and joint interfaces that occur
in more than one product (= candidates for "compatible" parts in a simulator).

Usage
  python build_catalog.py models/ -o catalog.json
  python build_catalog.py models/ -o catalog.json --products products-us.jsonl --specs specs/ \
         --names names/ --save-parts parts_glb/

Folder conventions (all optional, matched by article number or by file stem):
  specs/<article>.json   dimension spec for fit_dimensions (see fit_dimensions.py)
  names/<article>.json   rename map for split_parts (see split_parts.py)

Requires: numpy, scipy, pygltflib, DracoPy
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from fit_dimensions import compare
from ikea_glb import Model, read_glb, write_glb
from split_parts import analyze, build_tree, piece_info

ARTICLE = re.compile(r"(?<!\d)(\d{8})(?!\d)")


# ---------------------------------------------------------------------------- part features
def shape_axes(pts: np.ndarray):
    """Principal axes: returns (extents_cm sorted desc, main_axis unit vector)."""
    c = pts - pts.mean(0)
    _, _, vt = np.linalg.svd(c, full_matrices=False)
    ext = np.ptp(c @ vt.T, axis=0) * 100
    order = np.argsort(-ext)
    main = vt[order[0]]
    if main[np.argmax(np.abs(main))] < 0:
        main = -main                                   # consistent sign
    return ext[order], main


def part_record(p: dict) -> dict:
    ext, axis = shape_axes(p["pts"])
    rec = piece_info(p)
    rec.update({"kind": p["kind"], "length_cm": round(float(ext[0]), 1),
                "thickness_cm": [round(float(ext[1]), 1), round(float(ext[2]), 1)],
                "main_axis": np.round(axis, 3).tolist()})
    if p["group"] == "Hardware":
        # approximate fastener size in mm: diameter x length (from the principal extents)
        d_mm, l_mm = round(float(ext[1]) * 10), round(float(ext[0]) * 10)
        rec["hardware_mm"] = {"diameter": d_mm, "length": l_mm}
        rec["hardware_key"] = f"{p['kind']} Ø{d_mm}x{l_mm}"
    return rec


# ---------------------------------------------------------------------------- joints
def find_joints(pieces: list[dict], tol_m: float) -> list[dict]:
    trees = [cKDTree(p["pts"]) for p in pieces]
    joints = []
    for i, j in itertools.combinations(range(len(pieces)), 2):
        a, b = pieces[i], pieces[j]
        if np.any(a["min"] - tol_m > b["max"]) or np.any(b["min"] - tol_m > a["max"]):
            continue
        d, _ = trees[j].query(a["pts"], distance_upper_bound=tol_m)
        near_a = a["pts"][np.isfinite(d)]
        if len(near_a) < 2:
            continue
        d2, _ = trees[i].query(b["pts"], distance_upper_bound=tol_m)
        contact = np.concatenate([near_a, b["pts"][np.isfinite(d2)]])
        c = contact - contact.mean(0)
        _, _, vt = np.linalg.svd(c, full_matrices=False) if len(contact) >= 3 else (None, None, np.eye(3))
        span = np.ptp(c @ vt.T, axis=0) * 100                  # contact patch extents, cm
        hw = "Hardware" in (a["group"], b["group"])
        if hw:
            kind = "fastener"
        elif span[1] < 1.5:
            kind = "end-in-socket"                             # small patch: spindle end, leg top, peg
        else:
            kind = "surface"
        # interface key: rounded patch size, used to find similar joints across products
        key = f"{kind} {round(span[0])}x{round(span[1])}cm"
        joints.append({"a": a["name"], "b": b["name"], "a_id": a["id"], "b_id": b["id"], "kind": kind,
                       "contact_points": int(len(contact)), "point_cm": np.round(contact.mean(0) * 100, 1).tolist(),
                       "normal": np.round(vt[2], 3).tolist(), "patch_cm": np.round(span[:2], 1).tolist(),
                       "interface_key": key})
    return joints


def assembly_order(parts: list[dict], joints: list[dict]) -> list[str]:
    """A plausible build order: start from the largest non-hardware part, add neighbours breadth-first,
    hardware right after the parts it connects."""
    adj = defaultdict(set)
    for j in joints:
        adj[j["a"]].add(j["b"]); adj[j["b"]].add(j["a"])
    group = {p["part"]: p["group"] for p in parts}
    size = {p["part"]: p["triangles"] for p in parts}
    order, seen = [], set()
    for start in sorted((p["part"] for p in parts if p["group"] != "Hardware"), key=lambda n: -size[n]):
        if start in seen:
            continue
        queue = [start]; seen.add(start)
        while queue:
            n = queue.pop(0); order.append(n)
            for m in sorted(adj[n], key=lambda m: (group[m] == "Hardware", -size[m])):
                if m not in seen:
                    seen.add(m); queue.append(m)
    order += [p["part"] for p in parts if p["part"] not in seen]   # isolated pieces
    return order


# ---------------------------------------------------------------------------- products dataset
def load_products(path: str | None) -> dict:
    if not path:
        return {}
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            out[str(r["product_id"]).zfill(8)] = r
    return out


def product_info(row: dict | None) -> dict:
    if not row:
        return {}
    tree = row.get("category_tree") or []
    price = str(row.get("price", "")).replace(",", "")
    return {"title": (row.get("title") or "").replace(" - IKEA US", ""),
            "category": tree[1:-1], "price_usd": float(price) if re.fullmatch(r"[\d.]+", price) else None,
            "materials": row.get("materials", []), "url": row.get("source_url")}


# ---------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("-o", "--out", default="catalog.json")
    ap.add_argument("--products", help="products-us.jsonl from the Hugging Face IKEA dataset")
    ap.add_argument("--specs", help="folder of <article>.json dimension specs")
    ap.add_argument("--names", help="folder of <article>.json rename maps")
    ap.add_argument("--save-parts", help="folder to write each product's split GLB")
    ap.add_argument("--contact-mm", type=float, default=2.0, help="max gap counted as touching (default 2 mm)")
    ap.add_argument("--weld", type=float, default=0.1)
    args = ap.parse_args()

    files = sorted(Path(args.folder).glob("*.glb"))
    if not files:
        raise SystemExit(f"No .glb files in {args.folder}")
    products_db = load_products(args.products)
    if args.save_parts:
        Path(args.save_parts).mkdir(parents=True, exist_ok=True)

    def find_side_file(folder, art, stem):
        if not folder:
            return None
        for key in (art, stem):
            if key and (Path(folder) / f"{key}.json").exists():
                return json.loads((Path(folder) / f"{key}.json").read_text(encoding="utf-8"))
        return None

    catalog, hw_index, iface_index = [], defaultdict(list), defaultdict(list)
    for f in files:
        t0 = time.time()
        m = ARTICLE.search(f.stem)
        art = m.group(1) if m else None
        try:
            model = read_glb(str(f))
            names = find_side_file(args.names, art, f.stem)
            pieces = analyze(model, args.weld, 1, names)
        except Exception as e:                                  # keep going on a bad file
            print(f"  ! {f.name}: {e}")
            catalog.append({"id": art or f.stem, "file": f.name, "error": str(e)})
            continue
        allpts = np.concatenate([p["pts"] for p in pieces])
        size = (allpts.max(0) - allpts.min(0)) * 100
        parts = [part_record(p) for p in pieces]
        joints = find_joints(pieces, args.contact_mm / 1000)
        rec = {"id": art or f.stem, "article": art, "file": f.name,
               **product_info(products_db.get(art)),
               "overall_cm": {"width": round(float(size[0]), 1), "height": round(float(size[1]), 1), "depth": round(float(size[2]), 1)},
               "n_parts": len(parts),
               "groups": {g: sum(p["group"] == g for p in parts) for g in dict.fromkeys(p["group"] for p in parts)},
               "parts": parts, "joints": joints, "assembly_order": assembly_order(parts, joints)}

        tree = build_tree(f.name, pieces, args.weld)
        split_model = Model([tree], model.gltf, model.blob)    # part names are usable in specs
        spec = find_side_file(args.specs, art, f.stem)
        if spec:
            try:
                rows, _ = compare(split_model, spec["dimensions"], "none")
                rec["spec_check"] = [{k: r[k] for k in ("label", "spec_cm", "model_cm", "diff_cm", "diff_pct")} for r in rows]
            except SystemExit as e:                             # bad part name etc.: note it, keep going
                rec["spec_check_error"] = str(e)
                print(f"  ! {f.name} spec: {e}")
        if args.save_parts:
            out = Path(args.save_parts) / f"{f.stem}_parts.glb"
            write_glb(str(out), model, [tree])
            rec["parts_glb"] = str(out)

        for p in parts:
            if "hardware_key" in p:
                hw_index[p["hardware_key"]].append({"product": rec["id"], "part": p["part"]})
        for j in joints:
            iface_index[j["interface_key"]].append({"product": rec["id"], "a": j["a"], "b": j["b"]})
        catalog.append(rec)
        print(f"  {f.name}: {len(parts)} parts, {len(joints)} joints"
              f"{', spec ' + str(len(rec['spec_check'])) + ' dims' if rec.get('spec_check') else ''}"
              f"{', ' + rec['title'] if rec.get('title') else ''}  ({time.time() - t0:.1f}s)")

    shared = lambda idx: {k: v for k, v in sorted(idx.items()) if len({x["product"] for x in v}) > 1}
    out = {
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "source_folder": str(Path(args.folder).resolve().name),
        "conventions": "cm; glTF +Y up, +Z front; left/right as seen from the front",
        "n_products": len(catalog),
        "products": catalog,
        "hardware_index": dict(sorted(hw_index.items())),
        "shared_hardware": shared(hw_index),
        "shared_interfaces": shared(iface_index),
    }
    Path(args.out).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\n{len(catalog)} products -> {args.out}  "
          f"({len(out['shared_hardware'])} hardware sizes and {len(out['shared_interfaces'])} joint types shared by 2+ products)")


if __name__ == "__main__":
    main()
