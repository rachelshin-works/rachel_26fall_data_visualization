## i) Summary

| Layer                      | Dataset                                                                                             | Producer                             | Format               | Status | License                                        |
| -------------------------- | --------------------------------------------------------------------------------------------------- | ------------------------------------ | -------------------- | ------ | ---------------------------------------------- |
| Land                       | Viele, _Sanitary & Topographical Map of the City and Island of New York_ (1865) via NYPL Map Warper | Egbert L. Viele; rectified via NYPL  | GeoTIFF              | V      | Public domain (map); CC0 (Map Warper data)     |
| Land                       | Collect Pond outline                                                                                | digitized by me                      | GeoPackage / GeoJSON | V      | -                                              |
| Buildings                  | NYPL Building Inspector footprints (1857, 1894)                                                     | NYPL Labs / NYC Space/Time Directory | GeoJSON              | V      | CC0                                            |
| Buildings                  | MapPLUTO (present day)                                                                              | NYC Dept. of City Planning           | Shapefile / GeoJSON  | V      | NYC Open Data Terms of Use                     |
| People 1850/1880/1910/1950 | IPUMS USA Full Count, 1850 & 1880 (New York County)                                                 | IPUMS, University of Minnesota       | CSV                  | V      | IPUMS USA terms — **no redistribution**        |
| People 1850/1880           | NYC City Directories (Doggett's, Trow's)                                                            | NYPL (scans; Space/Time entries)     | NDJSON / scans       | -      | Public domain scans; check dataset license     |
| People 1850/1880           | Tenement House Committee report & maps (1894)                                                       | NY State Tenement House Committee    | Scans → table        | -      | Public domain                                  |
| People 1850/1880           | 97 Orchard Street (Dolkart, _Biography of a Tenement House_, 2006)                                  | Andrew S. Dolkart                    | Book → table         | -      | Copyrighted; facts extracted for analysis only |
| People 1910–               | NY State census, ward-level counts                                                                  | NY State                             | Table                | -      | Public domain (government publication)         |
| People 1910–               | NYPL apartment floor plans                                                                          | NYPL Digital Collections             | Images → table       | -      | Public domain (pre-1929 items)                 |
| (Boundaries)               | `nyc-wards` — Manhattan ward boundaries 1703–1895                                                   | NYC Space/Time Directory             | GeoJSON              | -      | CC0                                            |

---

## ii). Data sources

### 2.1 Viele Sanitary & Topographical Map (1865)

- **Producer:** Egbert L. Viele (cartographer); digitized and rectified through NYPL Map Warper
- **Location:** NYPL Map Warper — `https://maps.nypl.org/warper/` (add map ID)
- **Contents:** Manhattan's original streams, marshes, shoreline, and made land. Used to locate Collect Pond and the low wet ground around Five Points.
- **Manageable?** Yes. A single GeoTIFF (~\_\_ MB).

### 2.2 Collect Pond outline (my digitization)

- **Producer:** Traced in QGIS from 1.1 (EPSG:2263)
- **Contents:** Polygon(s) of the historic pond and its outlet.

### 2.3 NYPL Building Inspector

- **Producer:** NYPL Labs (crowdsourced verification of polygons vectorized from insurance atlases)
- **Location:** NYC Space/Time Directory — `https://spacetime.nypl.org` (dataset `building-inspector`)
- **Contents:** Historical building footprints with addresses and building info, from Perris (1857) and later (1894) atlas sheets.
- **Manageable?** Yes (clipping the focused area needed)

### 2.4 MapPLUTO

- **Producer:** NYC Department of City Planning
- **Location:** `https://www.nyc.gov/site/planning/data-maps/open-data.page`
- **Version:** \__ (e.g., 25v_)
- **Contents:** One record per tax lot: land use, building class, year built, number of floors, residential units.

### 2.5 IPUMS USA Full Count — 1850, 1880, 1910, 1950

- **Producer:** IPUMS USA, University of Minnesota
- **Location:** `https://usa.ipums.org` → Select Samples → USA FULL COUNT
- **Extract:** submitted 2026-11-05
- **Contents:** One record per person in the census, limited to New York State / New York County (Manhattan) using Select Cases.
- **Variables (34):** YEAR, SAMPLE(sample identifier), SERIAL(household serial number), NHWT(household wieght), GQ(group quarters status), COUNTYICP(County, ICPSR code, identifiable counties only), CITY, PERNUM(person number in sample unit), PERWT(Person weight), VERSIONHIST(Relase version for historical full counts), HISTID(Consistent historical data person identifier), FAMSIZE, RACE, RACED, BPL(birthplace), BPLD, MBPL(Mother's birthplace), FBPL(Fater's birthplace), NATIVITY, CITIZEN, YRIMMIG, LANGUAGE, LANGUAGED, OCC1950(occupation, 1950 basis)
- **Manageable?** Too large for GitHub, and the license issue is available. Kept locally.

### 2.6 NYC City Directories (Doggett's, Trow's)

- **Producer:** Original publishers (Doggett, Trow); scanned by NYPL; entries extracted by the NYC Space/Time Directory
- **Location:** NYPL Digital Collections; `https://github.com/nypl-spacetime` (city-directories)
- **Contents:** One entry per listed resident or business: name, occupation, and address. Used to place people on streets where the census does not.

### 2.7 Tenement House Committee report and maps (1894)

- **Producer:** New York State Tenement House Committee
- **Contents:** Density, nationality, and sanitary conditions by block or ward. I am transcribing the relevant tables by hand.

### 2.8 97 Orchard Street (Dolkart 2006)

- **Producer:** Andrew S. Dolkart, _Biography of a Tenement House in New York City_
- **Contents:** Plans and occupancy of a typical tenement. Used to build a "typical plan" reference table: rooms, area, and occupants.

### 2.9 NY State census, ward level (1915 / 1925)

- **Producer:** New York State
- **Contents:** Population by ward and nativity.

### 2.10 NHGIS 1910 tract data + 1950 tract shapefile

- **Producer:** IPUMS NHGIS
- **Location:** `https://www.nhgis.org`
- **Contents:** Census tract tables (population, nativity) and tract boundary polygons for New York City.

### 2.11 NYPL apartment floor plans

- **Producer:** NYPL Digital Collections (e.g., _Apartment Houses of the Metropolis_, 1908)
- **Contents:** Floor plans of early-1900s apartments. Hand-coded into a table of rooms, unit counts, and light/air features.

### 1.12 `nyc-wards` (boundaries)

- **Producer:** NYC Space/Time Directory
- **Location:** `https://spacetime.nypl.org` (dataset `nyc-wards`)
- **Contents:** Manhattan ward boundaries, 1703–1895. Gives the Sixth Ward polygon for 1850 and 1880.

---

## 2. Size and structure

| Dataset                | Rows                | Columns | One row =            | Key columns (type)                                                                        | Time          | Geography       | Last updated / next update                    |
| ---------------------- | ------------------- | ------- | -------------------- | ----------------------------------------------------------------------------------------- | ------------- | --------------- | --------------------------------------------- |
| Viele GeoTIFF          | ** × ** px, 3 bands | —       | a pixel              | RGB (uint8)                                                                               | 1865          | Manhattan       | Static (historical)                           |
| Collect Pond           | \_\_                | \_\_    | a pond polygon       | geometry                                                                                  | ca. 1800      | Five Points     |                                               |
| Building Inspector     | \_\_                | \_\_    | a building footprint | geometry (polygon), address (str), year (int), sheet ID (str)                             | 1857, 1894    | Lower Manhattan | Project archived; no further updates expected |
| MapPLUTO               | \_\_                | ~90     | a tax lot            | BBL (str), LandUse (cat), YearBuilt (int), NumFloors (float), UnitsRes (int)              | current       | NYC             | Released several times a year                 |
| IPUMS 1850             | \_\_                | 34      | a person             | YEAR (int), SERIAL (int), BPL (cat), RACE (cat), OCC1950 (cat), AGE (int), ENUMDIST (cat) | 1850          | Manhattan       | IPUMS version \_\_                            |
| IPUMS 1880             | \_\_                | 34      | a person             | same                                                                                      | 1880          | Manhattan       | same                                          |
| IPUMS 1910             | \_\_                | 34      | a person             | same + YRIMMIG (int), LANGUAGE (cat), CITIZEN (cat)                                       | 1910          | Manhattan       | same                                          |
| City directories       | \_\_                | \_\_    | a directory listing  | name (str), occupation (str), address (str), year (int)                                   | 1850s–1880s   | Manhattan       | Static                                        |
| Tenement report (hand) | \_\_                | \_\_    | a block or ward      | population (int), nationality counts (int)                                                | 1894          | Lower Manhattan | Mine                                          |
| 97 Orchard (hand)      | \_\_                | \_\_    | an apartment unit    | rooms (int), area_sqft (float), occupants (int)                                           | 1863–1935     | 1 building      | Mine                                          |
| NHGIS 1910 tracts      | \_\_                | \_\_    | a census tract       | GISJOIN (str), population (int), foreign-born (int)                                       | 1910          | NYC             | NHGIS version \_\_                            |
| Floor plans (hand)     | \_\_                | \_\_    | an apartment plan    | rooms (int), units per floor (int)                                                        | ca. 1900–1910 | Manhattan       | Mine                                          |

**Coordinate system:** all vector layers should have to be reprojected to **EPSG:2263**

**Important geographic limits**

- The **public** IPUMS full count has coded variables only. **Names and street addresses are not included**; they require a separate restricted-use license. Because of this, the smallest place unit I can use from IPUMS is the **enumeration district (ENUMDIST)**, where available. Addresses come from the city directories instead.
- In 1850 the questions on parents' birthplace (MBPL, FBPL) and on immigration year, citizenship, and language were not asked. Those variables are blank for 1850. YRIMMIG, CITIZEN, and LANGUAGE are blank for 1880 too.

---

## 3. Licensing and terms of use

| Dataset                                     | Status                                   | Attribution                            | Modify             | Redistribute                                               | Commercial                  | Terms                                                                       |
| ------------------------------------------- | ---------------------------------------- | -------------------------------------- | ------------------ | ---------------------------------------------------------- | --------------------------- | --------------------------------------------------------------------------- |
| Viele map (1865)                            | Public domain                            | Credit NYPL (courtesy)                 | Yes                | Yes                                                        | Yes                         | https://www.nypl.org/research/collections/digital-collections/public-domain |
| Map Warper / Building Inspector / nyc-wards | **CC0**                                  | Not required (courtesy credit to NYPL) | Yes                | Yes                                                        | Yes                         | https://spacetime.nypl.org                                                  |
| MapPLUTO                                    | NYC Open Data                            | Credit NYC DCP                         | Yes                | Yes                                                        | Yes                         | https://www.nyc.gov/home/terms-of-use.page                                  |
| IPUMS USA Full Count                        | Licensed, free for research and teaching | **Required citation** (see below)      | Yes (for analysis) | **No.** Raw full-count data may not be redistributed.      | Research and education only | https://www.ipums.org/about/terms                                           |
| IPUMS NHGIS                                 | Licensed, free                           | **Required citation**                  | Yes                | **No**, without permission                                 | —                           | https://www.nhgis.org/research/citation                                     |
| City directory scans                        | Public domain                            | Credit NYPL                            | Yes                | Yes                                                        | Yes                         | NYPL Digital Collections                                                    |
| Tenement House Committee (1894)             | Public domain (government, pre-1929)     | Cite the report                        | Yes                | Yes                                                        | Yes                         | —                                                                           |
| Dolkart (2006)                              | **Copyrighted**                          | Cite the book                          | Facts only         | I share my derived table, not images or text from the book | No                          | —                                                                           |
| NYPL floor plans                            | Public domain (pre-1929 items)           | Credit NYPL                            | Yes                | Yes                                                        | Yes                         | NYPL Digital Collections                                                    |

**What this means for the repo**

- IPUMS and NHGIS raw files stay **local only** and are listed in `.gitignore`. The repo contains the extract definition (samples, variables, case selection) so anyone can request the same extract, plus **aggregated** tables (counts by district and birthplace). It does not contain person-level rows.
- Required citations:
  - Steven Ruggles et al. \_IPUMS USA: Version \_\_\_ [dataset]. Minneapolis, MN: IPUMS, 20**. https://doi.org/10.18128/D010.V**
  - Steven Manson et al. _IPUMS National Historical Geographic Information System: Version 21.0_ [dataset]. Minneapolis, MN: IPUMS, 2026. http://doi.org/10.18128/D050.V21.0

<!-- ---

## 4. Descriptive statistics

Generated with `describe_data.py`. Output tables are saved in `outputs/stats/`.

### 4.1 IPUMS (People) — key variables

**Numerical: AGE**

| Year | n   | min | 25% | median | mean | 75% | max | range | std | skew |
| ---- | --- | --- | --- | ------ | ---- | --- | --- | ----- | --- | ---- |
| 1850 |     |     |     |        |      |     |     |       |     |      |
| 1880 |     |     |     |        |      |     |     |       |     |      |
| 1910 |     |     |     |        |      |     |     |       |     |      |

**Numerical: FAMSIZE** (same table)

**Categorical: BPL (birthplace)** — top 10 per year

| Year | Unique | #1  | #2  | #3  | …   | Unknown / missing |
| ---- | ------ | --- | --- | --- | --- | ----------------- |
| 1850 |        |     |     |     |     |                   |
| 1880 |        |     |     |     |     |                   |
| 1910 |        |     |     |     |     |                   |

**Categorical: RACE** — counts per year, with special attention to _Chinese_ (very small in 1880).

**Categorical: OCC1950** — top 10 occupations; share coded _N/A_ or _non-occupational response_.

**Time:** records per YEAR. Note that there are gaps between census years: no data between 1850 and 1880 or between 1880 and 1910.

**Geography: ENUMDIST**

- Unique districts per year: \_\_
- Largest and smallest districts by population: \_\_
- Districts in the Five Points / Sixth Ward area: \_\_ (list)
- Districts expected but missing: \_\_

### 4.2 Building Inspector (Buildings)

- Footprints per year (1857 vs 1894): \_\_
- Footprint area in sq ft: min / 25% / median / mean / 75% / max / std
- Building material or class categories: unique count, top categories, share missing
- Atlas sheets covering the study area: \_\_

### 4.3 MapPLUTO (Buildings, today), clipped to the study area

- Lots: \_\_
- YearBuilt: earliest and latest, share of lots with 0 (unknown), lots built before 1900
- NumFloors and UnitsRes: summary statistics
- LandUse: counts by category

### 4.4 Hand-built tables

- Tenement report: blocks covered, mean persons per block, nationality shares
- 97 Orchard: units, rooms per unit, occupants per unit (range)
- Floor plans: number of plans coded, rooms per unit

### 4.5 What I learned

_(answer after running the stats)_

- What does a typical person record look like in each year?
- Which birthplaces dominate in each year, and how fast does the mix change?
- How small are the Chinese counts in 1880? Can they be mapped at the district level without being misleading?
- Are there outliers? For example, very large households are often boarding houses or institutions (check GQ).
- What surprised me?

--- -->

## 4. Data problems and how I will handle them

| Problem                                    | Where                                                           | What I will do                                                                                                                                |
| ------------------------------------------ | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| No names or addresses in public full count | IPUMS                                                           | Map at the enumeration-district or ward level. Use city directories for street-level points. Keep the restricted-license request as optional. |
| Questions not asked in some years          | IPUMS 1850 (MBPL, FBPL), 1850/1880 (YRIMMIG, CITIZEN, LANGUAGE) | Use BPL and RACE as the shared axis across all years. Add second-generation analysis for 1880 and 1910 only.                                  |
| Unknown or missing codes                   | BPL, OCC1950                                                    | Report counts; keep them as an "Unknown" category instead of dropping them.                                                                   |
| Transcription errors                       | IPUMS full count, directory OCR                                 | Check unexpected values (e.g., AGE > 110, impossible birthplaces) and flag them. Leave them in the data but exclude from rates.               |
| Very small counts                          | RACE = Chinese, 1880                                            | Do not compute percentages for tiny groups. Show raw counts or aggregate to ward level.                                                       |
| Institutions and group quarters            | GQ                                                              | Filter or flag group quarters so prisons, hospitals, and lodging houses do not distort household density.                                     |
| Changing boundaries                        | Wards (1850–1880), EDs (each census), tracts (1910 vs 1920)     | Map each year on its own boundaries. Compare years visually instead of forcing one common unit.                                               |
| Georeferencing error                       | Viele map                                                       | Rectified with local control points around Five Points. Residual error is about \_\_ ft. Treat pond edges as approximate.                     |
| Duplicate or overlapping footprints        | Building Inspector                                              | Check for duplicate geometries per sheet and remove exact duplicates.                                                                         |
| Unknown year built                         | PLUTO (YearBuilt = 0)                                           | Treat as missing, not as year 0.                                                                                                              |
| Inconsistent categories                    | Directory occupations (free text)                               | Group into broad classes by hand (labor, trade, merchant, etc.).                                                                              |
| Hand-entry error                           | Tenement report, 97 Orchard, floor plans                        | Double-check totals against the published sums.                                                                                               |
