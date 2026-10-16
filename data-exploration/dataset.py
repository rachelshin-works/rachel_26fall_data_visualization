import os, re
import pandas as pd

if os.path.exists("products-us.jsonl"):
    df = pd.read_json("products-us.jsonl", lines=True, dtype={"product_id": str})
else:
    from datasets import load_dataset
    df = load_dataset("jeffreyszhou/ikea-us-products-2025", split="train").to_pandas()

n = len(df)
pct = lambda k: f"{k:,} ({k / n:.1%})"
df["price_num"] = pd.to_numeric(df["price"].astype(str).str.replace(",", ""), errors="coerce")
p = df["price_num"]

print(f"Rows: {n:,}   unparseable prices: {p.isna().sum()}")
print(f"Price min {p.min():.2f} | max {p.max():.2f} | range {p.max() - p.min():.2f}")
print(f"Price mean {p.mean():.2f} | median {p.median():.2f}")
bins = pd.cut(p, [0, 10, 100, 500, float("inf")], right=False,
              labels=["<$10", "$10-100", "$100-500", "$500+"])
for k, v in bins.value_counts().sort_index().items():
    print(f"  {k}: {pct(v)}")

top = df["category_tree"].apply(lambda t: t[1] if len(t) > 1 else "(uncategorized)")
print(f"\nTop-level categories: {top.nunique()}")
print(df.assign(top=top).groupby("top")["price_num"]
      .agg(count="size", median="median", min="min", max="max")
      .sort_values("count", ascending=False).to_string())
print(f"\nUnique leaf categories: {df['category_tree'].apply(lambda t: t[-1]).nunique():,}")
print(f"Unique product families: {df['title'].str.split().str[0].nunique():,}")

bundle = df["source_url"].str.contains(r"-s\d{8}/?$")
print(f"Bundles (s-prefixed IDs): {pct(bundle.sum())}")
mats = df["materials"].apply(lambda m: " ".join(m))
print(f"Mentions recycled content: {pct(mats.str.contains('recycled', case=False).sum())}")
care = df["care_instructions"].apply(lambda c: " ".join(c))
print(f"Tested for public use: {care.str.contains('public use', case=False).sum():,}")
print(f"Duplicate titles: {df['title'].duplicated().sum():,}")
print(f"Duplicate image paths: {df['image_urls'].str[0].duplicated().sum():,}")

if not os.path.exists("products-us.jsonl"):
    df.drop(columns=["price_num"]).to_json(
        "products-us.jsonl", orient="records", lines=True, force_ascii=False)
    print("\nSaved products-us.jsonl")

light = pd.DataFrame({
    "product_id": df["product_id"],
    "family": df["title"].str.split().str[0],
    "title": df["title"].str.replace(" - IKEA US", "", regex=False),
    "category": top,
    "price": df["price_num"],
    "bundle": bundle,
}).dropna(subset=["price"])
light.to_json("ikea_prices.json", orient="records", force_ascii=False, indent=1)
print(f"Saved ikea_prices.json ({len(light):,} rows)")