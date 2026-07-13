# Data Source Feasibility Audit Report

Generated at: 2026-07-13 13:31:59

## Executive Summary

This report evaluates the feasibility of data acquisition from **13** critical public databases across the Delhi NCR region.

| Status | Count | Description |
| --- | --- | --- |
| **IMPLEMENTED** | 1 | Ready for automated ingestion (e.g. APIs, static endpoints) |
| **PARTIAL** | 1 | Semi-automated extraction implemented |
| **MANUAL DOWNLOAD REQUIRED** | 6 | Protected by CAPTCHAs, bot blocks, or multi-step form submissions |
| **BLOCKED** | 0 | Restricted access or legally constrained sources |

> [!NOTE]
> RERA portals and circle rates frequently fall into `MANUAL_DOWNLOAD_REQUIRED` due to CAPTCHA protections and PDF-only distribution formats. This project builds reproducible manual adapters rather than bypassing security mechanisms.

## Detailed Source Audit Registry

| Source ID | Source Name | Geography | Category | Format | Access Method | Feasibility | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `nhb_residex` | NHB RESIDEX | National / NCR | baseline | XLSX | html | MEDIUM | **PARTIAL** | Tracks housing price index (HPI) based on both assessment prices and market prices. NHB publishes... |
| `up_rera` | UP RERA Project Disclosures | Uttar Pradesh | rera | HTML | html | LOW | **MANUAL_DOWNLOAD_REQUIRED** | Contains cost, size, pricing proxy details for registered residential projects. Web portals prote... |
| `hrera_gurugram` | Haryana RERA Gurugram | Haryana | rera | HTML | html | LOW | **MANUAL_DOWNLOAD_REQUIRED** | Covers Gurugram district projects. Web portals protect details with CAPTCHAs. Automation is parti... |
| `hrera_panchkula` | Haryana RERA Panchkula Jurisdiction | Haryana | rera | HTML | html | LOW | **MANUAL_DOWNLOAD_REQUIRED** | Covers Faridabad and other Haryana NCR districts. Web portals protect details with CAPTCHAs. Auto... |
| `delhi_rera` | Delhi RERA | Delhi | rera | HTML | html | LOW | **NOT_AUDITED** | Delhi real estate is dominated by DDA and standalone redevelopment rather than large RERA project... |
| `delhi_circle_rates` | Delhi Government Circle Rates | Delhi | circle_rates | PDF | pdf | LOW | **MANUAL_DOWNLOAD_REQUIRED** | Categorized by locality category (A to H). Requires mapping categories to candidate localities. C... |
| `up_circle_rates` | Uttar Pradesh Circle Rates (IGRS UP) | Uttar Pradesh | circle_rates | PDF | manual_download | LOW | **MANUAL_DOWNLOAD_REQUIRED** | Requires manual retrieval per district (Gautam Buddha Nagar, Ghaziabad) and text extraction. Circ... |
| `haryana_collector_rates` | Haryana Collector Rates | Haryana | circle_rates | PDF | manual_download | LOW | **MANUAL_DOWNLOAD_REQUIRED** | Collector rates vary by sector/village. Highly localized. Circle rates are published in PDF docum... |
| `pib_news` | Press Information Bureau (PIB) | National / NCR | infrastructure | JSON | api | HIGH | **IMPLEMENTED** | Excellent for establishing official project approval dates and event timelines. PIB press release... |
| `dmrc_metro` | Delhi Metro Rail Corporation (DMRC) | Delhi / NCR | infrastructure | HTML | html | HIGH | **NOT_AUDITED** | DMRC covers Delhi and extensions to Noida, Ghaziabad, Gurugram, Faridabad. |
| `nmrc_metro` | Noida Metro Rail Corporation (NMRC) | Noida / Greater Noida | infrastructure | HTML | html | HIGH | **NOT_AUDITED** | Tracks Aqua line history. |
| `ncrtc_rrts` | National Capital Region Transport Corporation (NCRTC) | NCR | infrastructure | HTML | html | HIGH | **NOT_AUDITED** | Tracks Namo Bharat progress. |
| `nhai_projects` | NHAI / MoRTH Projects | National / NCR | infrastructure | HTML | html | HIGH | **NOT_AUDITED** | Covers Dwarka Expressway, Yamuna Expressway, FNG, Delhi-Dehradun, etc. |

## Feasibility Analysis & Recommendations

### 1. Real Estate Price Data (The Price Proxy Problem)
- **Circle Rates**: High manual intervention is required. PDFs must be periodically downloaded per district (Noida, Gurugram, Delhi) and compiled into spatial lookup tables.
- **RERA Filings**: Excellent for project details, but bulk price details are locked behind JS grids or CAPTCHAs. Recommended approach: compile raw data from manual quarterly downloads or sample RERA filings to construct composite project price proxies.
- **NHB RESIDEX**: Reliable regional HPI trends are available in Excel format. This will serve as our quarterly baseline normalization index.

### 2. Infrastructure Project Milestones
- **DMRC/NMRC/NCRTC**: General timelines are obtainable via press releases and official site histories. PIB is highly valuable as a structured text feed for timeline reconstruction (cabinet approval, funding, construction start, commissioning dates).
