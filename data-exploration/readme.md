# IKEA US Products (July 2025) — Data Exploration

---

## Step 2 — Dataset documentation

| Item                       | Detail                                                                                                                                                                                                                                                                                                     |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Dataset name**           | IKEA US Product Dataset (July 2025) — `ikea-us-products-2025`                                                                                                                                                                                                                                              |
| **Source / organization**  | Compiled by Jeffrey Zhou, published on Hugging Face. Underlying content scraped from IKEA US (ikea.com/us) product pages.                                                                                                                                                                                  |
| **URL**                    | https://huggingface.co/datasets/jeffreyszhou/ikea-us-products-2025                                                                                                                                                                                                                                         |
| **Date accessed**          | 10.15.2026                                                                                                                                                                                                                                                                                                 |
| **Brief description**      | A structured snapshot of ~30,000 products sold on IKEA's US website: product name and size, marketing description, category breadcrumb, price, materials, care instructions, "good to know" notes, a product page URL, one image per product. Built by crawling IKEA's `sitemap.xml` filtered to US pages. |
| **Time period covered**    | Single snapshot, scraped at July 2025. No time series.                                                                                                                                                                                                                                                     |
| **Geographic coverage**    | US market only (USD, inch system).                                                                                                                                                                                                                                                                         |
| **Number of rows**         | **30,511** (one row per product / product variant)                                                                                                                                                                                                                                                         |
| **Number of columns**      | **11** (`product_id`, `title`, `description`, `category_tree`, `style`, `image_urls`, `source_url`, `price`, `good_to_know`, `materials`, `care_instructions`)                                                                                                                                             |
| **File format**            | CSV(downloaded csv through python script)                                                                                                                                                                                                                                                                  |
| **License / terms of use** | Listed as **MIT**. The dataset card notes that descriptions, images and trademarks belong to IKEA, that the data is for research and non-commercial use, and that IKEA's own terms apply to any wider use.                                                                                                 |

---

## Step 3 — Exploring the Data

### i) overview

| Variable            | Type                             | Role           | Notes                                                                                                             |
| ------------------- | -------------------------------- | -------------- | ----------------------------------------------------------------------------------------------------------------- |
| `product_id`        | ID (string)                      | Key            |                                                                                                                   |
| `title`             | Text                             | Name + variant | Pattern: `NAME type, color/finish, size - IKEA US`. Product family, color and **_dimensions_** can be parsed out. |
| `description`       | Text                             | Marketing copy | usually repeating the title.                                                                                      |
| `category_tree`     | List (categorical)               | Hierarchy      | Breadcrumb path, e.g. `Products › Tables & chairs › Dining furniture › Dining chairs`.                            |
| `style`             | Categorical                      | —              | Empty                                                                                                             |
| `image_urls`        | List (path)                      | Media          | One image path per row                                                                                            |
| `source_url`        | URL                              | Link           | IKEA US product page.                                                                                             |
| `price`             | **Numerical** (stored as string) | Measure        | USD                                                                                                               |
| `good_to_know`      | List (text)                      | Notes          | Assembly, "sold separately", included parts, technical specs.                                                     |
| `materials`         | List (text)                      | Composition    | Mostly broken down **_part by part_**, with recycled content: `Top panel/ Side panel: Solid pine, Acrylic paint`. |
| `care_instructions` | List (text)                      | Maintenance    | Some include safety certifications.                                                                               |

**Numerical:** `price` (directly); derived counts — number of materials, number of care steps, category depth, dimensions parsed from `title`, % recycled parsed from `materials`.

**Categorical:** `category_tree` levels (top-level department → leaf type), product family name (first word of `title`), color/finish (from `title`), material types (from `materials`).

### ii) Interesting variables

- **`materials`** — It describes products as assemblies of named parts (top panel, drawer side, leg, midbeam…) with a material for each. This is a text-based "parts list" that links directly to my IKEA assembly-instruction project: it can approximate how many components and material types a piece of furniture has.
- **Recycled content** inside `materials` (e.g. `min. 50% recycled`, `100% recycled`) — a measurable sustainability signal hidden in free text.
- **`care_instructions` certifications** — some seating carries notes like "tested for **public use** … EN 16139 / ANSI/BIFMA x5.4." That separates domestic furniture from furniture rated for public/contract settings, relevant to my interest in public seating.
- **`good_to_know` "sold separately" / "included in the price but packaged separately"** — shows how products are split across boxes and dependent on other products (system furniture like SEKTION/METOD kitchens).
- **`category_tree`** — lets me see how IKEA organizes the domestic world, and how deep each branch goes.

### iii) Missing or unusual values

- **`style` is empty** — drop it.
- **Price as a string**, with mixed formatting (`549` vs `9.99`)--needs casting.
- **Broken fractions in titles:** dimensions sometimes lose their fraction characters, e.g. `181/2x161/8"` actually means `18 ½ × 16 ⅛"`, while other rows render correctly (`8 ¼x11 ¾"`). Dimension parsing has to handle both.
- **Leaf category glued together:** the last breadcrumb element joins name and type without a space — `YTTERVÅGNightstand`, `ZEBRASÄVPendant lamp`.
- **Repeated breadcrumb levels:** e.g. `Dining chairs › Dining chairs`.
- **Empty lists** (`[]`) instead of nulls for `materials`, `good_to_know`, `care_instructions` — the "no nulls" statistic hides real missingness.
- **Inconsistent capitalization / wording** within one family: `VOXTORP drawer front, matte white` vs `VOXTORP Drawer front, white matt white`.
- **Descriptions start by repeating the title**, so text analysis should strip it first.

### iv) Potential problems and limitations

- **Variants inflate counts.** Every color and size is its own row (e.g. YTTERVÅG bed frame appears as 14+ rows across colors, sizes and included slat bases). Counts of "products" overstate distinct designs — need to group by family name.
- **Bundles double-count.** Combination products (IDs prefixed `s` in the URL) contain parts that are also sold individually; same materials/images may repeat.
- **Shared images:** different variants (e.g. Queen vs King) can point to the same image file.
- **Single 2025 data** — no change over time, no sales, ratings, or stock data; prices may already be out of date.

---

## Step 4 — Potential Questions

Rather than treating the dataset only as a price list, these questions read the semi-structured text fields (categories, materials, notes, care instructions, descriptions) as evidence of how IKEA organizes, assembles, connects and narrates domestic life.

1. **IKEA classify the home as:** _(distribution / hierarchy)_
   What hierarchy does IKEA use to divide domestic life into departments and types, which branches hold the most products, and where are prices concentrated?
   - `category_tree`, `price`
   - successful visualization then I expected
2. **What are IKEA objects made of, part by part?** _(relationships between variables + further potential development)_
   Which named components (top panel, back panel, leg, drawer side…) are made from which materials?
   - `materials` parsed into `part → material` pairs
   - visualization should have to be considered
3. **Which products stand alone or cannot stand alone** _(relationships / unusual observations)_
   Which products depend on other products that are "sold separately" or "included but packaged separately," and what hidden ecosystems (lighting, kitchens, beds) does that network reveal?
   - `good_to_know` — product names in capitals matched against the list of product families
     visualization should have to be considered
4. **How much care does an object ask for?** _(comparison between groups)_
   Which categories and materials demand the most maintenance, and what language of care do the instructions use (wipe, wash, do not…)?
   - `care_instructions` (number of steps, verbs), joined with category and material
   - data cleaning needed
5. **Does each room have its own (marketing) language?** _(comparison / text patterns)_
   Which words and adjectives does IKEA use to sell each department (e.g. "cozy" for bedrooms, "easy" for kitchens), and which words are shared across the whole catalog?
   - `description` (with the repeated title removed), grouped by top-level category
   - the worst idea and the outcome...
