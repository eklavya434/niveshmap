# Analytical Methodology

## 1. Unit of Observation
The primary unit of analysis for the forecasting model is:
$$\text{Locality} \times \text{Quarter}$$

Every record in the processed panel represents the state of a single locality (e.g., *Noida Sector 150*) during a specific calendar quarter (e.g., *2022-Q3*).

---

## 2. The Price Proxy Problem
Residential real estate in Delhi NCR lacks a centralized public transaction database. The platform uses a **Composite Price Proxy** strategy:
1. **Circle / Collector Rates**: Represent the official baseline level but are static step-functions (updated infrequently).
2. **RERA filings**: Disclose actual project pricing at time of registration but suffer from sparse updates.
3. **NHB RESIDEX**: Provides a dynamic, quarterly Housing Price Index (HPI) at the city level.

### Pricing Strategy
The composite proxy uses circle rates as the structural baseline levels, and adjusts them dynamically using normalized city-level growth curves derived from the NHB RESIDEX.

---

## 3. Temporal Integrity (Anti-Leakage)
To prevent look-ahead bias, features representing transit infrastructure are dynamically computed based on the state of the project as of that quarter.

### Leakage Protection Logic
For each event in the project timeline, we preserve:
* `event_date`: The actual date of the physical event (e.g., construction start).
* `article_publish_date`: The official release/publication date of the news.

An event is only marked as active in a historical quarter if:
$$\text{event\_date} \le \text{quarter\_end} \quad \text{AND} \quad \text{article\_publish\_date} \le \text{quarter\_end}$$

This prevents models from training on construction events that were not yet public knowledge or had not yet happened.

---

## 4. Data Readiness Framework
Localities are audited and dynamically classified into eligibility tiers to maintain statistical defense:
* **FULL_FORECAST_ELIGIBLE**: Strong price provenance + complete temporal infrastructure events + $\ge 20$ quarters of data.
* **LIMITED_FORECAST_ELIGIBLE**: Usable price proxies + $\ge 12$ quarters of data.
* **INTELLIGENCE_ONLY**: Failed price depth/provenance but contains geospatial coordinate completeness and infrastructure project proximity.
* **INSUFFICIENT_COVERAGE**: Neither price nor infrastructure records are analytically useful.

---

## 5. No Causal Claims
This platform models scenario-conditioned correlations and trends. It **does not claim causality** (e.g., "building a metro line causes a 12% rise in sector prices") because it is impossible to control for all latent variables in NCR real estate (commercial developments, developer premiums, macroeconomic trends). The forecasting outputs are scenario-conditioned forecasts, not causal inferences.
