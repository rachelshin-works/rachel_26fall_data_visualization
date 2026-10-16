"""Build the five JSON files used by the D3 charts in this folder.

Usage (from this folder):
    pip install pandas datasets
    python prepare_viz_data.py                 # downloads from Hugging Face
    python prepare_viz_data.py products-us.jsonl   # or use a local copy

Writes to ./data/:
    catalog_tree.json        Q1  How does IKEA classify the home?
    parts_materials.json     Q2  What are IKEA objects made of, part by part?
    dependency_network.json  Q3  Which products cannot stand alone?
    care.json                Q4  How much care does an object ask for?
    marketing_words.json     Q5  Does each room have its own marketing language?
"""
import json, os, re, sys
from collections import Counter, defaultdict
import pandas as pd

OUT = "data"
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- load
src = sys.argv[1] if len(sys.argv) > 1 else ("products-us.jsonl" if os.path.exists("products-us.jsonl") else None)
if src:
    df = pd.read_json(src, lines=True, dtype={"product_id": str})
else:
    from datasets import load_dataset
    df = load_dataset("jeffreyszhou/ikea-us-products-2025", split="train").to_pandas()
for col in ["category_tree", "good_to_know", "materials", "care_instructions"]:
    df[col] = df[col].apply(lambda v: list(v) if v is not None else [])

df["price_num"] = pd.to_numeric(df["price"].astype(str).str.replace(",", ""), errors="coerce")
df["family"] = df["title"].str.split().str[0].str.upper()
df["top"] = df["category_tree"].apply(lambda t: t[1] if len(t) > 1 else "(Uncategorized)")
print(f"Loaded {len(df):,} rows")


def save(name, obj):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  wrote data/{name}")


def med(s):
    s = s.dropna()
    return None if s.empty else round(float(s.median()), 2)


# ---------------------------------------------------------------- Q1 catalog tree
# Hierarchy: department > sub-department > type (3 levels below "Products").
# The last breadcrumb element is the product itself (e.g. "YTTERVÅGNightstand"), so it is dropped.
def path(tree):
    levels = tree[1:-1] if len(tree) > 2 else tree[1:]
    out = []
    for lv in levels:                      # drop repeated levels ("Dining chairs > Dining chairs")
        if not out or out[-1] != lv:
            out.append(lv)
    return (out or ["(Uncategorized)"])[:3]

df["path"] = df["category_tree"].apply(path)
root = {"name": "IKEA US", "children": {}}
for p, price, title in zip(df["path"], df["price_num"], df["title"]):
    node = root
    for lv in p:
        node = node["children"].setdefault(lv, {"name": lv, "children": {}, "_prices": [], "_titles": []})
    node["_prices"].append(price)
    if len(node["_titles"]) < 3:
        node["_titles"].append(title.replace(" - IKEA US", ""))

def finish(node):
    """Returns (json_node, all prices underneath). Every node gets count + median price."""
    kids, all_prices = [], list(node.get("_prices", []))
    for c in node["children"].values():
        k, p = finish(c)
        kids.append(k)
        all_prices += p
    own = node.get("_prices", [])
    out = {"name": node["name"], "count": len(all_prices), "median": med(pd.Series(all_prices, dtype=float))}
    if kids:
        if own:   # products filed directly at a non-leaf level become a leaf of their own
            kids.append({"name": f"{node['name']} (other)", "value": len(own), "count": len(own),
                         "median": med(pd.Series(own, dtype=float)), "examples": node["_titles"]})
        out["children"] = kids
    else:
        out.update(value=len(own), examples=node["_titles"])
    return out, all_prices

save("catalog_tree.json", finish(root)[0])


# ---------------------------------------------------------------- Q2 parts -> materials
def clean_material(m):
    m = re.sub(r"\(.*?\)", "", m)                 # (min. 50% recycled)
    m = re.sub(r"\d+\s*%", "", m)                  # 100 % polyester
    m = re.sub(r"\d+(\.\d+)?\s*lb/cu\.?ft\.?", "", m)
    return re.sub(r"\s+", " ", m).strip(" .,").lower()

pair_counts, part_counts, mat_counts = Counter(), Counter(), Counter()
unlabeled = 0
for mats in df["materials"]:
    seen = set()
    for entry in mats:
        if ":" not in entry:
            unlabeled += 1
            continue
        parts_str, mat_str = entry.split(":", 1)
        parts = [p.strip().lower() for p in parts_str.split("/") if p.strip()]
        materials = [clean_material(m) for m in mat_str.split(",")]
        for p in parts:
            for m in materials:
                if m and (p, m) not in seen:        # count each pair once per product
                    seen.add((p, m))
                    pair_counts[(p, m)] += 1
for (p, m), c in pair_counts.items():
    part_counts[p] += c
    mat_counts[m] += c

TOP_PARTS, TOP_MATS = 14, 14
parts = [p for p, _ in part_counts.most_common(TOP_PARTS)]
mats = [m for m, _ in mat_counts.most_common(TOP_MATS)]
links = [{"source": p, "target": m, "value": c}
         for (p, m), c in pair_counts.items() if p in parts and m in mats and c >= 5]
save("parts_materials.json", {
    "nodes": [{"id": p, "side": "part"} for p in parts] + [{"id": m, "side": "material"} for m in mats],
    "links": links,
    "note": f"{unlabeled:,} material entries had no named part and are excluded.",
})


# ---------------------------------------------------------------- Q3 dependency network
families = set(df["family"])
STOP = {"IKEA", "LED", "USB", "ANSI", "BIFMA", "UL", "AC", "DC", "CFM", "FSC", "PEFC", "GU10", "E26", "E12"}
CAPS = re.compile(r"\b[A-ZÅÄÖÆØÜÉ]{3,}\b")
RANK = {"sold separately": 3, "included": 2, "mentioned": 1}
edges = defaultdict(lambda: {"count": 0, "type": "mentioned"})
for fam, notes in zip(df["family"], df["good_to_know"]):
    for note in notes:
        low = note.lower()
        kind = "sold separately" if "sold separately" in low else "included" if "included" in low else "mentioned"
        for tok in set(CAPS.findall(note)):
            if tok in families and tok != fam and tok not in STOP:
                e = edges[(fam, tok)]
                e["count"] += 1
                if RANK[kind] > RANK[e["type"]]:
                    e["type"] = kind

fam_info = df.groupby("family").agg(
    products=("product_id", "size"),
    median=("price_num", "median"),
    category=("top", lambda s: s.mode().iat[0]),
)
links = [{"source": s, "target": t, **v} for (s, t), v in edges.items()]
links.sort(key=lambda l: -l["count"])
links = links[:600]                                 # keep the strongest ties readable
ids = {l["source"] for l in links} | {l["target"] for l in links}
out_deg = Counter(l["source"] for l in links)
in_deg = Counter(l["target"] for l in links)
nodes = []
for f in ids:
    role = "both" if out_deg[f] and in_deg[f] else "needs others" if out_deg[f] else "needed by others"
    info = fam_info.loc[f]
    nodes.append({"id": f, "role": role, "category": info["category"], "products": int(info["products"]),
                  "median": None if pd.isna(info["median"]) else round(float(info["median"]), 2),
                  "in": in_deg[f], "out": out_deg[f]})
save("dependency_network.json", {"nodes": nodes, "links": links})


# ---------------------------------------------------------------- Q4 care
MAX_STEPS = 12
LEAD_CLAUSE = ("for ", "to ", "in ", "if ", "when ", "after ", "before ", "during ", "since ", "as ")
SKIP_WORDS = {"to", "be", "please", "always", "carefully", "only", "regularly", "then", "also", "it", "is", "should"}
NOT_VERBS = {"information", "the", "this", "a", "an", "all", "use", "recommended"}  # "use" kept below as a verb

def verb(instr):
    """Return the action word an instruction opens with, e.g. 'wipe', 'do not bleach', 'machine wash'."""
    s = instr.strip()
    head = s.split(":", 1)
    if len(head) == 2 and len(head[0]) <= 30:      # "Removable cover: Machine wash ..."
        s = head[1].strip()
    low = s.lower()
    if low.startswith(LEAD_CLAUSE) and "," in low:  # "For increased stability, re-tighten ..." -> "re-tighten ..."
        low = low.split(",", 1)[1].strip()
    words = re.findall(r"[a-z]+(?:-[a-z]+)?", low)
    while words and words[0] in SKIP_WORDS:         # "To be washed separately" -> "washed"
        words = words[1:]
    if not words:
        return None
    if words[:2] == ["do", "not"] and len(words) > 2:
        return "do not " + words[2]
    if words[0] in ("never", "avoid") and len(words) > 1:
        return "do not " + words[1] if words[0] == "never" else "avoid"
    if words[0] == "machine" and len(words) > 1:
        return "machine " + words[1]
    if words[0] in NOT_VERBS - {"use"} or words[0] in PREPOSITIONS:
        return None                                 # a note, not an action ("Only for decoration")
    return PARTICIPLES.get(words[0], words[0])

PREPOSITIONS = {"for", "to", "in", "with", "on", "at", "by", "from", "not", "suitable", "of"}
PARTICIPLES = {"washed": "wash", "cleaned": "clean", "dried": "dry", "wiped": "wipe", "ironed": "iron"}

df["care_n"] = df["care_instructions"].apply(len)
cats = df["top"].value_counts()
cats = [c for c in cats.index if cats[c] >= 100 and c != "(Uncategorized)"]
care_rows = []
for c in cats:
    sub = df[df["top"] == c]
    dist = sub["care_n"].clip(upper=MAX_STEPS).value_counts().sort_index()
    care_rows.append({"category": c, "n": len(sub), "median": float(sub["care_n"].median()),
                      "mean": round(float(sub["care_n"].mean()), 2),
                      "none": int((sub["care_n"] == 0).sum()),
                      "dist": [{"steps": int(k), "count": int(v)} for k, v in dist.items()]})
care_rows.sort(key=lambda r: -r["mean"])
verbs = Counter(v for lst in df["care_instructions"] for v in map(verb, lst) if v)
save("care.json", {"maxSteps": MAX_STEPS, "categories": care_rows,
                   "verbs": [{"verb": v, "count": c} for v, c in verbs.most_common(20)]})


# ---------------------------------------------------------------- Q5 marketing words
STOPWORDS = set("""a an the and or but if of to in on at by for with from as is are was were be been being it its
this that these those you your yours we our us they them their there here than then so such can could will would
should may might must also just all any each every both more most other some no not only own same too very into
over under about up down out off again once while when where why how which who whom what one two three four
inch inches cm mm ft lb oz x s t don make makes made get gets let lets use used using do does""".split())
fam_lower = {f.lower() for f in families}
WORD = re.compile(r"[a-z]+(?:['’][a-z]+)?")

def words_of(title, desc):
    t = title.replace(" - IKEA US", "")
    d = desc[len(t):] if desc.startswith(t) else desc       # drop the repeated title
    toks = set(WORD.findall(d.lower()))
    return {w for w in toks if len(w) > 2 and w not in STOPWORDS and w not in fam_lower and "'" not in w and "’" not in w}

df["words"] = [words_of(t, d) for t, d in zip(df["title"], df["description"])]
word_cats = [c for c in df["top"].value_counts().index if c != "(Uncategorized)"][:12]
sub = df[df["top"].isin(word_cats)]
overall = Counter(w for ws in sub["words"] for w in ws)
N = len(sub)
per_cat = {c: Counter(w for ws in sub.loc[sub["top"] == c, "words"] for w in ws) for c in word_cats}
n_cat = sub["top"].value_counts().to_dict()

chosen = [(w, "shared") for w, _ in overall.most_common(10)]
picked = {w for w, _ in chosen}
for c in word_cats:                                  # 2 most distinctive words per category
    scores = []
    for w, k in per_cat[c].items():
        share = k / n_cat[c]
        if share >= 0.05 and overall[w] >= 30 and w not in picked:
            scores.append((share / (overall[w] / N), w))
    for _, w in sorted(scores, reverse=True)[:2]:
        chosen.append((w, "distinctive"))
        picked.add(w)

cells = [{"category": c, "word": w, "count": per_cat[c][w], "pct": round(100 * per_cat[c][w] / n_cat[c], 1)}
         for c in word_cats for w, _ in chosen]
save("marketing_words.json", {
    "categories": [{"category": c, "n": int(n_cat[c])} for c in word_cats],
    "words": [{"word": w, "kind": k, "overallPct": round(100 * overall[w] / N, 1)} for w, k in chosen],
    "cells": cells,
})
print("Done. Start a local server here (python -m http.server) and open the .html files.")
