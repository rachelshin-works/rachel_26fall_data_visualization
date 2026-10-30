# Made land, made low

Data Visualization | Rachel Shin | 10.29.2026

## Overview

Collect Pond, once the main source of fresh water in Manhattan, was filled in the 1810s, and the land it left behind became the lowest, wettest ground in lower Manhattan. Buildings settled, cellars flooded, and residents who could afford to leave did so. The land became cheap, and the neighborhood became the first stop for new arrivals. The sequence of residents ran from Irish and German immigrants and Black New Yorkers, to Italians and Eastern European Jews, to Chinese residents along Mott, Pell, and Doyers Streets. The filled ground also became the site of the city’s largest jail, the Tombs. The neighborhood was “the bottom” in elevation and in the city’s social order. The pattern continues. On the site of the old Tombs jail, the city is building a 335-foot jail, the tallest ever. And as tenement families once packed into windowless rooms, New Yorkers now split apartments with flex walls. Why is the bottom of the city still built for confinement and compression? This atlas traces both through maps, through a data visualization of how people lived inside its tenements, compared room by room with the uptown apartments built at the same time, and through the voices of people living in this area.

## Questions

From 1850 to 1910, who lived on the land made by filling Collect Pond, and how did that population changes as Five Points became Chinatown--and what’s their narratives and stories beneath it? How they lived?

Who recorded this neighborhood, and what did they leave out? Most of what we know about Five Points came from outsiders: reformers, journalists. City directories, archaeology, and a few oral interviews offer some of a view from inside. The atlas places the two kinds of record side by side.

| | | 
| --- | --- |
| 1. Where exactly was Collect Pond, and how far does the made land extend? | Georeference the Viele Sanitary & Topographical Map in QGIS and trace the pond, the marsh, and the old waterways as polygons. |
| 2. Who lived here in 1850, 1880, 1910, 1930, and today, and how did they live? | Combine building data (footprints, materials, and use from fire insurance atlases and PLUTO) with census data to understand residents’ race, birthplace, occupation, and living conditions in each period. The geographic unit changes across years: 19th-century census only at the county level, and NYC census tracts begin in 1920. Geocoding individual addresses for 1850 and 1880 from IPUMS, using ward-level reports for 1910, and using NHGIS tract data for 1930 are needed. |
| 3. Layering major events and personal stories alongside the data | Start from the atlas's 1894 footprints on the made land. Set them beside uptown apartment plans from 1908 to 1910 at the same scale. Code both the same way: rooms per unit, persons per room, windowless rooms, baths, room names. |

## Precednts

| Mapping Historical New York: | Mapping Inequality: | Nonstop Metropolis (Rebecca Solnit): |
| --- | --- | --- |
| Maps individual residents from census record. | Pairs HOLC maps with the original assessor’s descriptions, showing how institutions labeled “bad” neighborhoods. | Pairs essays with thematic maps |

- Richard Plunz, *A History of Housing in New York City*
- Elizabeth Collins Cromley, *Alone Together: A History of New York's Early Apartments*
- Tyler Anbinder, *Five Points*

## Datasets

✓: checked | - : pending

| Layer | Data | Status |
| --- | --- | --- |
| Land | Viele Sanitary & Topographical Map (1865), NYPL Map Warper | GeoTIFF ✓ |
| Buildings | NYPL Building Inspector (1857, 1894, PLUTO) | Footprint, material (1857&1894 mapping completed) ✓ |
| People 1850/1880 | IPUMS full-count<br>City Directory (Doggett’s, Trow’s)<br>Tenement House Committee report and maps<br>97 Orchard Street, in Dolkart's Biography of a Tenement House < data hand formation required | Birthplace, occupation, address (data checking needed - requested, waiting for the response) -<br>Density, nationality, typical plans |
| People 1910~ | NY State census ward<br>NHGIS tract + 1920 tract shapefile<br>NYPL apartment floor plans < data hand formation required | Birthplace, occupation, address (data checking needed - requested, waiting for the response) - |
