# Limitations

This document outlines the limitations identified during **Phase 0: Data Feasibility Audit**.

## 1. Price Data Constraints
* **Step-Function Circle Rates**: Circle rates are adjusted infrequently (often remaining static for 2–5 years). They do not capture quarterly market supply/demand fluctuations.
* **Absence of Transaction Ledger**: There is no public transaction ledger. Listing prices from portals are highly inflated and contain duplicates. The composite price proxy is an index trend, not a true transaction rate.
* **Lack of Jurisdiction Standardization**: Haryana, Uttar Pradesh, and Delhi use different circle rate methodologies (collector rates vs. category classes), making absolute comparisons difficult. Price values must be indexed relative to a baseline quarter.

## 2. Ingestion & Automation Restrictions
* **CAPTCHA blocks**: UP RERA and HRERA portals protect detail screens with CAPTCHAs, preventing direct, fully automated crawling. We must utilize manual quarterly bulk downloads or reproducible file adapters.
* **Anti-Bot Protection**: Bypassing anti-bot controls or CAPTCHAs is explicitly avoided. Ingestion adapters are designed to process local snapshot formats.

## 3. Geospatial Features
* **Haversine Distance**: Distance metrics are straight-line/geodesic distances. They do not account for road-network configurations, traffic flow, or actual gate-to-gate driving times.
* **Locality Boundaries**: Localities are represented by centroids. Large sectors (e.g. Sector 150) cover several square kilometers, meaning actual transit station distances can vary by 1–2 km depending on where a project is situated within that sector.

## 4. Modeling Limitations
* **Look-ahead Bias**: Modelers must strictly partition timestamps to ensure future stages do not contaminate historical rows.
* **Non-Causality**: The scenario models present correlations and trend associations, not mathematical proofs of causality.
