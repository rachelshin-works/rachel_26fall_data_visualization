# IKEA GLB tools

Python scripts for IKEA web 3D models (the `.glb` you get from the product page's 3D viewer).

| file | what it does |
|---|---|
| `split_parts.py` | splits a merged model into its physical parts (legs, rails, bolts, screws…) → `*_parts.glb` + `*_parts.json` |
| `fit_dimensions.py` | measures the model against the product's published dimensions, optionally rescales it, embeds the numbers → `*_dims.glb` + `*_dims.csv` |
| `build_catalog.py` | runs both steps on a whole folder of GLBs → one `catalog.json` (parts, joints, build order, spec check, product info, shared-hardware index) |
| `ikea_glb.py` | shared reader/writer (Draco decoding, GLB writing). Not run directly. |
| `parts_viewer.html` | exploded view of a `*_parts.glb` |
| `dimension_viewer.html` | dimension lines + drawing-vs-model table for a `*_dims.glb` |
| `examples/` | `skogsta_names.json` (rename map), `lustebo_spec.json`, `skogsta_spec.json` (dimension specs) |

## Setup
    pip install -r requirements.txt

## 1. Split into parts
    python split_parts.py skogsta.glb
    python split_parts.py skogsta.glb -o skogsta_parts.glb --names examples/skogsta_names.json

- Parts = pieces whose triangles are not connected to anything else (welded at 0.1 mm; change with `--weld`).
- Automatic names come from shape + position: `Panel horizontal`, `Leg front left`, `Post`, `Rail`, `Bolt/screw`, `Nut/fitting`, `Screw head/washer`, `Body`.
- To rename: open the printed table or `*_parts.json`, then write a names file keyed by automatic name or id (`P01`…):
  `{"Panel horizontal front": {"name": "Seat", "group": "Seat"}}`
- Each part node has its pivot at the part's centre and extras `part_id, part, group, auto_name, triangles, size_cm, center_cm`.
- Limits: pieces that are fused in the mesh stay together (e.g. LUSTEBO frame + seat shell = one `Body`). Cut those in Blender.

## 2. Match the dimensions
    python fit_dimensions.py lustebo_parts.glb examples/lustebo_spec.json
    python fit_dimensions.py lustebo_parts.glb examples/lustebo_spec.json --fit uniform

- `--fit none` (default) only measures; `uniform` applies one scale factor (median of the overall-size ratios); `axes` scales X/Y/Z separately (distorts the shape).
- Spec measures: `size` (axis x/y/z), `top`, `bottom`, `between` (two edges), `width_at` (extent within a height band). `parts` selects part names from split_parts.py; omit it for the whole model. See the docstring in `fit_dimensions.py`.
- Works on unsplit files too, using `"parts": "prim:0"`, `"prim:1"`… for the original mesh primitives.

## 3. Many models → one catalog.json
    models/      50544867-mini.glb, 70541165-mini.glb, ...   (article number anywhere in the file name)
    specs/       50544867.json ...   (optional, fit_dimensions spec per product)
    names/       50544867.json ...   (optional, rename map per product)

    python build_catalog.py models -o catalog.json --products products-us.jsonl --specs specs --names names --save-parts parts_glb

Per product: `overall_cm`, `parts[]` (size, shape axis, length/thickness, hardware Ø×length mm),
`joints[]` (which parts touch, where, contact normal, kind: `fastener` / `end-in-socket` / `surface`, `interface_key`),
`assembly_order` (breadth-first from the largest part), `spec_check` (if a spec exists), and title/category/price/materials
joined from the Hugging Face dataset by article number. Top level: `hardware_index`, `shared_hardware`, `shared_interfaces`
(sizes/joint types found in 2+ products — starting points for compatibility).
Joints = parts closer than `--contact-mm` (default 2 mm). Kinds and sizes are geometric estimates, not IKEA data.

## 4. Look at the results
    python -m http.server
    → http://localhost:8000/parts_viewer.html?file=skogsta_parts.glb
    → http://localhost:8000/dimension_viewer.html?file=lustebo_parts_dims.glb

Conventions: glTF meters, +Y up, +Z = front of the furniture, "left/right" as seen from the front.
Models and drawings © IKEA — non-commercial coursework/research only.
