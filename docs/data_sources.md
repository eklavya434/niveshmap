# Data Sources Directory

The platform utilizes and audits public data sources across Central Government and local NCR state jurisdictions.

## 1. Regional & Central Sources
* **NHB RESIDEX**:
  * **Category**: Baseline Index
  * **Access Method**: Excel download
  * **Format**: XLSX
  * **Description**: Tracks quarterly Housing Price Indices (HPI) based on both assessment prices and market transaction samples. Used to compute regional baseline trends.
* **Press Information Bureau (PIB)**:
  * **Category**: Infrastructure timeline
  * **Access Method**: Text queries via PIB Search API
  * **Format**: JSON
  * **Description**: Archival feed of Cabinet approvals, financial sanctions, and project status announcements.

## 2. Uttar Pradesh NCR Sources
* **UP RERA**:
  * **Category**: Project pricing disclosures & milestones
  * **Access Method**: HTML (public portal protected by CAPTCHAs)
  * **Format**: HTML
  * **Description**: Noida, Greater Noida, Ghaziabad residential project registrations and quarterly progress reports.
* **IGRS UP**:
  * **Category**: Transaction records / Circle rates
  * **Access Method**: Manual PDF downloads
  * **Format**: PDF
  * **Description**: Sector-wise circle rates published by District Magistrates.

## 3. Haryana NCR Sources
* **Haryana RERA (HRERA) Gurugram / Panchkula**:
  * **Category**: Project pricing disclosures
  * **Access Method**: HTML (requires dynamic JS rendering)
  * **Format**: HTML
  * **Description**: Filings for residential projects in Gurugram (Gurugram jurisdiction) and Faridabad (Panchkula jurisdiction).
* **Haryana Collector Rates**:
  * **Category**: Circle rates
  * **Access Method**: Manual PDF download from district websites
  * **Format**: PDF
  * **Description**: Annual collector rates published per sector/village in Gurugram and Faridabad.

## 4. Delhi Sources
* **Delhi RERA**:
  * **Category**: Project pricing disclosures
  * **Access Method**: HTML portal
  * **Format**: HTML
  * **Description**: Small coverage area due to high prevalence of standalone redevelopment rather than large-scale private townships.
* **Delhi Revenue Department**:
  * **Category**: Circle rates
  * **Access Method**: PDF download
  * **Format**: PDF
  * **Description**: Category-based circle rates (A to H categories) mapped spatially to candidate localities.
