# Feature Feasibility Matrix

Evaluates the feasibility and completeness of potential predictive features across NCR jurisdictions.

| Feature Name | Required Source | Available | Historical Availability | Temporal Reconstruction | Missingness | Leakage Risk | Phase 0 Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `price_proxy` | circle_rates, rera, nhb | YES | 28 quarters (Delhi/Noida), 14-20 (Emerging) | YES | 0% to 45% | LOW | **PROVISIONALLY FEASIBLE** | Constructed as composite from circle rates and RERA disclosures. |
| `ncr_baseline` | nhb_residex | YES | 28+ quarters | YES | 0% | NONE | **FULLY FEASIBLE** | NHB Residex city indices serve as baselines. |
| `metro_stage` | dmrc, nmrc | YES | Full history | YES (via events) | 0% | HIGH (Protected) | **FULLY FEASIBLE** | Reconstructed from event dates and publication news. |
| `expressway_stage`| nhai | YES | Full history | YES (via events) | 0% | MEDIUM | **FULLY FEASIBLE** | Major corridor milestones. |
| `airport_stage` | pib, authorities | YES | Full history | YES (via events) | 0% | LOW | **FULLY FEASIBLE** | Handled Jewar and IGI timelines. |
| `distance_metro_km`| geocoded centroids | YES | Static | N/A | 0% | NONE | **FULLY FEASIBLE** | Haversine distance from centroid to stations. |
| `rera_project_count`| rera portals | PARTIAL | ~2018 onwards | NO | 15% | LOW | **LIMITED FEASIBLE** | Active registered project counts. |
