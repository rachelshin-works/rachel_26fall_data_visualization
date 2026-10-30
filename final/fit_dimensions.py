"""Compare an IKEA 3D model (GLB) with the product's published dimensions, and optionally rescale it to match.

  1. reads the GLB (Draco or plain, merged or already split with split_parts.py),
  2. measures every dimension listed in a spec JSON (overall size, seat height, part sizes ...),
  3. prints drawing vs. model, and with --fit rescales the model to the drawing,
  4. writes a GLB with the dimensions embedded in the root node's extras ("ikea_dimensions"),
     including dimension-line anchor points, plus a CSV report. dimension_viewer.html draws them.

Usage
  python fit_dimensions.py model.glb spec.json                  -> model_dims.glb + model_dims.csv
  python fit_dimensions.py model.glb spec.json --fit uniform    one scale factor for the whole model
  python fit_dimensions.py model.glb spec.json --fit axes       separate X/Y/Z factors (distorts shape)

spec.json
  { "product": "LUSTEBO chair",
    "source":  "IKEA US product page, dimension drawing",
    "dimensions": [
      {"label": "Width",       "spec_cm": 55, "measure": "size", "axis": "x"},
      {"label": "Height",      "spec_cm": 85, "measure": "size", "axis": "y"},
      {"label": "Seat height", "spec_cm": 46, "measure": "top",  "parts": "Panel horizontal"},
      {"label": "Seat width",  "spec_cm": 48, "measure": "size", "axis": "x", "parts": ["Panel horizontal", "Rail front"]},
      {"label": "Back height", "spec_cm": 38, "measure": "between",
         "from": {"parts": "Panel horizontal", "edge": "top"}, "to": {"edge": "top"}},
      {"label": "Back width",  "spec_cm": 40, "measure": "width_at", "above_cm": 80}
    ] }

measure:  size      extent of the selected parts along axis x | y | z
          top       height of the selection's highest point above the floor
          bottom    height of the selection's lowest point above the floor
          between   vertical distance between two edges ({"parts", "edge": top|bottom})
          width_at  extent along axis (default x) of points between above_cm and below_cm
parts:    omitted = whole model. A name or list of names, matched against node names, the
          part / auto_name / part_id stored by split_parts.py, or "prim:N" (N-th mesh primitive).
"fit": false on a dimension leaves it out of the scale calculation (default: only overall
          "size" dimensions with no parts are used to fit).

Conventions: glTF meters, +Y up, +Z = front. Requires numpy, pygltflib, DracoPy.
"""
from __future__ import annotations

import argparse
import csv
import json
from fractions import Fraction
from pathlib import Path

import numpy as np

from ikea_glb import TreeNode, apply, read_glb, write_glb

AXIS = {"x": 0, "y": 1, "z": 2}
FRACS = {Fraction(1, 8): "⅛", Fraction(1, 4): "¼", Fraction(3, 8): "⅜", Fraction(1, 2): "½",
         Fraction(5, 8): "⅝", Fraction(3, 4): "¾", Fraction(7, 8): "⅞"}


def inches(cm: float) -> str:
    eighths = round(cm / 2.54 * 8)
    whole, rest = divmod(eighths, 8)
    frac = FRACS.get(Fraction(rest, 8), "")
    return f"{whole}{' ' + frac if frac else ''}\""


# ---------------------------------------------------------------------------- selection
def collect(model):
    """List of (labels, world points) per mesh primitive."""
    out, k = [], 0
    for node, world in model.mesh_nodes():
        ex = node.extras or {}
        for p in node.prims:
            labels = {node.name, f"prim:{k}", str(ex.get("part", "")), str(ex.get("auto_name", "")), str(ex.get("part_id", ""))}
            out.append((labels - {""}, apply(world, p.attributes["POSITION"])))
            k += 1
    return out


def select(prims, parts) -> np.ndarray:
    if parts in (None, "*", []):
        return np.concatenate([p for _, p in prims])
    names = [parts] if isinstance(parts, str) else list(parts)
    hit = [p for labels, p in prims if labels & set(names)]
    if not hit:
        avail = sorted({l for labels, _ in prims for l in labels if not l.startswith("prim:")})
        raise SystemExit(f"No part matches {names}. Available: {', '.join(avail)}")
    return np.concatenate(hit)


# ---------------------------------------------------------------------------- measuring
def measure(d: dict, prims, scale: np.ndarray):
    """Return (value_m, anchor_from, anchor_to) in the scaled model's space."""
    S = lambda pts: pts * scale
    allp = S(select(prims, None))
    lo, hi = allp.min(0), allp.max(0)
    floor = lo[1]
    pad = 0.04
    m = d["measure"]
    sel = S(select(prims, d.get("parts")))
    smin, smax, sc = sel.min(0), sel.max(0), (sel.min(0) + sel.max(0)) / 2

    if m == "size":
        ax = AXIS[d.get("axis", "x")]
        v = smax[ax] - smin[ax]
        if ax == 0:
            a, b = [smin[0], smin[1], hi[2] + pad], [smax[0], smin[1], hi[2] + pad]
        elif ax == 1:
            a, b = [lo[0] - pad, smin[1], lo[2]], [lo[0] - pad, smax[1], lo[2]]
        else:
            a, b = [hi[0] + pad, smin[1], smin[2]], [hi[0] + pad, smin[1], smax[2]]
        return v, a, b
    if m in ("top", "bottom"):
        y = smax[1] if m == "top" else smin[1]
        return y - floor, [hi[0] + pad, floor, sc[2]], [hi[0] + pad, y, sc[2]]
    if m == "between":
        def edge(spec):
            pts = S(select(prims, spec.get("parts")))
            return pts[:, 1].max() if spec.get("edge", "top") == "top" else pts[:, 1].min()
        y1, y2 = edge(d["from"]), edge(d["to"])
        return abs(y2 - y1), [lo[0] - pad, min(y1, y2), sc[2]], [lo[0] - pad, max(y1, y2), sc[2]]
    if m == "width_at":
        ax = AXIS[d.get("axis", "x")]
        y0 = floor + d.get("above_cm", -1e9) / 100
        y1 = floor + d.get("below_cm", 1e9) / 100
        band = sel[(sel[:, 1] >= y0) & (sel[:, 1] <= y1)]
        if not len(band):
            raise SystemExit(f"'{d['label']}': no geometry between {d.get('above_cm')} and {d.get('below_cm')} cm")
        bmin, bmax = band.min(0), band.max(0)
        y = min(bmax[1] + 0.03, hi[1] + 0.03)
        a, b = bmin.copy(), bmax.copy()
        a[1] = b[1] = y
        other = 2 if ax == 0 else 0
        a[other] = b[other] = (bmin[other] + bmax[other]) / 2
        return bmax[ax] - bmin[ax], a.tolist(), b.tolist()
    raise SystemExit(f"Unknown measure '{m}' in '{d['label']}'")


def fit_scale(spec, prims, mode: str) -> np.ndarray:
    one = np.ones(3)
    if mode == "none":
        return one
    use = [d for d in spec if d.get("fit", d["measure"] == "size" and not d.get("parts"))]
    if not use:
        raise SystemExit("--fit needs at least one overall 'size' dimension (or set \"fit\": true on some)")
    ratios = [(d, d["spec_cm"] / 100 / measure(d, prims, one)[0]) for d in use]
    if mode == "uniform":
        return one * float(np.median([r for _, r in ratios]))
    s = one.copy()                                            # axes
    for ax, i in AXIS.items():
        rs = [r for d, r in ratios if d["measure"] == "size" and d.get("axis", "x") == ax]
        if rs:
            s[i] = float(np.median(rs))
    return s


# ---------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("glb")
    ap.add_argument("spec")
    ap.add_argument("-o", "--out")
    ap.add_argument("--fit", choices=["none", "uniform", "axes"], default="none")
    args = ap.parse_args()

    src = Path(args.glb)
    out_glb = Path(args.out) if args.out else src.with_name(src.stem + "_dims.glb")
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    dims = spec["dimensions"]
    model = read_glb(str(src))
    prims = collect(model)

    before = [measure(d, prims, np.ones(3))[0] for d in dims]
    scale = fit_scale(dims, prims, args.fit)
    rows = []
    for d, b in zip(dims, before):
        v, a, z = measure(d, prims, scale)
        rows.append({
            "id": d.get("id") or d["label"].lower().replace(" ", "_"),
            "label": d["label"], "measure": d["measure"],
            "spec_cm": d["spec_cm"], "spec_in": d.get("spec_in") or inches(d["spec_cm"]),
            "model_cm_before": round(b * 100, 1), "model_cm": round(v * 100, 1),
            "diff_cm": round(v * 100 - d["spec_cm"], 1),
            "diff_pct": round((v * 100 - d["spec_cm"]) / d["spec_cm"] * 100, 1),
            "from": [round(float(x), 4) for x in a], "to": [round(float(x), 4) for x in z],
            **({"label_t": d["label_t"]} if "label_t" in d else {}),
        })

    # print
    fitted = args.fit != "none"
    print(f"{src.name}  fit={args.fit}  scale x{scale[0]:.4f} y{scale[1]:.4f} z{scale[2]:.4f}\n")
    head = f"{'dimension':18} {'drawing':>8} " + (f"{'before':>8} " if fitted else "") + f"{'model':>8} {'diff':>7}"
    print(head + "\n" + "-" * len(head))
    for r in rows:
        print(f"{r['label'][:18]:18} {r['spec_cm']:>8} " + (f"{r['model_cm_before']:>8} " if fitted else "")
              + f"{r['model_cm']:>8} {r['diff_cm']:>+7.1f}")

    # write GLB: wrap the scene in a root that carries the scale + dimensions
    root = TreeNode(f"{src.stem} (dimensions)", scale=scale.tolist() if fitted else None,
                    extras={"ikea_dimensions": {
                        "product": spec.get("product", src.stem), "source": spec.get("source", ""),
                        "fit": args.fit, "scale": [round(float(s), 5) for s in scale],
                        "units": "anchors in glTF meters, in the root node's (scaled) space; values in cm",
                        "dimensions": rows}},
                    children=model.roots)
    # anchors are measured in scaled space; the viewer adds them to the scene root, not under the scaled node
    write_glb(str(out_glb), model, [root])
    csv_path = out_glb.with_suffix(".csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[k for k in rows[0] if k not in ("from", "to", "label_t")], extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    print(f"\nWrote {out_glb} and {csv_path}")


if __name__ == "__main__":
    main()
