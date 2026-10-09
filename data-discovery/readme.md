# Communal backyard

## Introduction

How owns the place, and how people shape the space?
I am interested in local communities, especially neighborhoods shaped by immigrants and migrants such as Downtown Brooklyn, Harlem, and Chinatown. I wanted to see where people in these neighborhoods gather and how those places have changed over time.
What I found is that no dataset records "community" directly. Every dataset records something else in its place: facilities, address listings, guidebooks, benches, or shops, and ended up picking five datasets made by different kinds of publishers (a city agency, a library, a community member, and a company)

| #   | Dataset                                      | Publisher                                        | Period       |
| --- | -------------------------------------------- | ------------------------------------------------ | ------------ |
| 1   | NYC Facilities Database (FacDB)              | NYC Department of City Planning                  | Present      |
| 2   | NYPL City Directories / Space/Time Directory | Commercial publishers, digitized by NYPL         | 1786–1922/23 |
| 3   | The Green Book                               | Victor Green, digitized by NYPL Schomburg Center | 1936–1966    |
| 4   | DOT Seating Locations                        | NYC Department of Transportation                 | Present      |
| 5   | Foursquare Open Source Places                | Foursquare                                       | Present      |

---

## 1. NYC Facilities Database (FacDB)

**About**
A database of more than 30,000 facilities and program sites that are owned, operated, funded, licensed, or certified by a city, state, or federal agency in New York City. Each record has a facility name, address, type, operating entity, and coordinates.

**Origin**
The NYC Department of City Planning (DCP) builds it by combining about 50 input files from city, state, and federal agencies and from non-profit organizations. It is updated twice a year.

**Purpose**
It is the base data for planning work: Fair Share analysis, neighborhood studies, and facilities planning. It is also meant to let New Yorkers see what government resources exist in their own neighborhoods.

**Takeaway**
Each agency classifies its facilities in its own way, and DCP regroups all of them into seven domains. That puts libraries, senior centers, and community centers on one map. It also shows what the government counts as the things that shape quality of life in a neighborhood.

**What are the issues? Where does it fall short?**

- Records are missing or duplicated, and some addresses point to a headquarters office instead of the actual service site.
- Some facilities are deliberately left out to protect the safety and privacy of their clients.
- DCP cannot confirm that every site is open to the public.
- It only includes places tied to government. Informal anchors of immigrant communities, such as hometown associations, temples, or gatherings in front of a shop, are not in it.

---

## 2. NYPL City Directories and the NYC Space/Time Directory

**About**
Scanned New York City directories from 1786 through 1922/23, listing the names and addresses of residents, churches, businesses, and schools. Entries from 1850 to 1890 have been extracted as JSON records with name, occupation, and address.

**Origin**
The originals were commercial books issued yearly by private publishers such as Doggett and Trow. The New York Public Library digitized them, and NYPL and NYU extracted the data as part of the NYC Space/Time Directory project.

**Purpose**
The directories were paid address books for finding people and businesses (the 1850/51 edition cost $2). NYPL digitized them so that anyone could read them for free instead of handling fragile originals, and so that researchers could build datasets that connect to maps and census records.

**Takeaway**
The census came once every ten years, but directories came out almost every year. Because occupation and address appear together, I can trace what kinds of people lived and worked on a particular street.

**What are the issues? Where does it fall short?**

- Only part of the population is listed. The 1850/51 edition recorded about 80,000 people when the city's population was about 696,000.
- Many women were not listed until they became widows.
- Coverage is essentially Manhattan, so Downtown Brooklyn needs a separate source.
- Only volumes published before 1923 were scanned, for copyright reasons.
- Structured data stops at 1890. Later years would have to be extracted by hand or with OCR.
- My assumption: non-English-speaking immigrants and renters were probably left out more often than others.

---

## 3. The Green Book (NYPL Schomburg Center)

**About**
A travel guide published from 1936 to 1966 that listed hotels, restaurants, beauty salons, nightclubs, and gas stations where Black travelers would be safe and welcome. The Schomburg Center digitized 21 volumes from 1937 to 1964. The 1947 and 1956 editions are available as data with coordinates.

**Origin**
Victor Green, a postal worker who lived in Harlem, published it. Listings grew through tips from readers and from fellow postal workers around the country. NYPL Labs extracted the 1947 data with OCR, and the 1956 data came from the University of South Carolina.

**Purpose**
A tool for traveling safely in an era of segregation, sundown towns, and lynching.

**Takeaway**
Of the five, it is the only dataset a community made for itself. It is a list of "places where we are welcome," not a government or corporate record. It began as a guide to the New York area, so Harlem is well represented through the documentation.

**What are the issues? Where does it fall short?**

- Only two years exist as structured data, and the OCR contains errors.
- A place appears only if a tip about it reached the publisher.
- Few of the New York City locations still exist, so a one-to-one comparison with today might difficult.
- NYPL stopped updating the map site in October 2024. The data now has to be downloaded from GitHub.

---

## 4. DOT Seating Locations

**About**
Locations of NYC DOT seating on sidewalks and at bus stops, including benches and leaning bars.

**Origin**
Published on NYC Open Data in November 2023. Last updated in September 2026.

**Purpose**
It is an inventory of street furniture that DOT installs and maintains. The underlying CityBench program aims to add public seating at bus stops, along retail corridors.

**Takeaway**
It shows where the city decided a seat was needed. _Overlaying bench locations with population or facility data for the three neighborhoods can reveal where seating is missing._

**What are the issues? Where does it fall short?**

- It only covers seating installed by DOT. Park benches, privately owned public spaces, and seating that residents bring out themselves (chairs, crates, vendor stools) are not included.
- It records location only, not who sits there or how often. Bench existing =/= a community gathers there

---

## 5. Foursquare Open Source Places

**About**
An open dataset of more than 100 million places of interest worldwide with 22 core attributes. Updated monthly and licensed under Apache 2.0, which allows commercial use.

**Origin**
Foursquare, a location technology company founded in 2009, released it in November 2024. The data is maintained by its Places Engine, which combines human confirmation with AI agents.

**Purpose**
It began as a proprietary asset for Foursquare's own apps and its advertising and data business. The company opened it because it believes that, without a distribution platform like Google Maps, an open source community is the best way to keep global place data accurate.

**Takeaway**
It includes small shops, restaurants, salons, and religious sites that government data does not, so it gives the densest picture of the commercial landscape. (A private company gave away a core asset is also a story worth telling.)

**What are the issues? Where does it fall short?**

- It leans toward commercial places, because the data comes from what app users and businesses registered.
- Closed businesses can linger in the data, and there are no historical snapshots.
- Access depends on company policy. Distribution has already moved to a new Places Portal.

---

## Sources

- [FacDB README, NYC Department of City Planning](https://www.nyc.gov/assets/planning/download/pdf/data-maps/open-data/facilities_readme.pdf?r=0622)
- [New York Public Library Digitizes 137 Years of New York City Directories](https://live-legacy-admin.nypl.org/blog/2016/09/21/new-york-city-directories-free-online)
- [New York City Directories Extracted Persons Entries, 1850–1890 (NYU)](https://archive.nyu.edu/bitstream/2451/61521/87/QuickGuide.pdf)
- [NYC Space/Time Directory (NYPL)](https://spacetime.nypl.org)
- [Navigating the Green Book (NYPL Labs)](https://publicdomain.nypl.org/greenbook-map)
- [Green Book data on GitHub (NYPL)](https://github.com/NYPL-publicdomain/greenbooks)
- [Mapping the Book that Guided Black Travelers Across a Segregated America (WNYC)](https://wnyc.org/story/mapping-green-book/)
- [Seating Locations, NYC Open Data](https://data.cityofnewyork.us/d/esmy-s8q5)
- [City Bench Locations (Historical), NYC Open Data](https://data.cityofnewyork.us/d/kuxa-tauh)
- [Foursquare Open Source Places announcement](https://foursquare.com/resources/blog/products/foursquare-open-source-places-a-new-foundational-dataset-for-the-geospatial-community/)
- [Evolving FSQ Open Source Places (Foursquare)](https://foursquare.com/resources/blog/data/evolving-fsq-open-source-places/)
