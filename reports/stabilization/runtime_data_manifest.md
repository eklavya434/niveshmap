# Runtime Data Manifest

This manifest documents all configuration, dataset, and model files loaded by the NiveshMap application during execution.

## Manifest Table

| Path | Loading Component | Type | Committed to Git | Behavior If Missing |
| :--- | :--- | :--- | :--- | :--- |
| [config/suitability.yaml](file:///c:/Users/eklav/Desktop/NiveshMap/config/suitability.yaml) | `src.ncr_intelligence.modeling.suitability` | YAML Config | Yes | Falls back gracefully to default internal dictionaries |
| [config/spatial.yaml](file:///c:/Users/eklav/Desktop/NiveshMap/config/spatial.yaml) | `src.ncr_intelligence.geospatial.spatial_intelligence` | YAML Config | Yes | App throws FileNotFoundError at startup |
| [config/localities.yaml](file:///c:/Users/eklav/Desktop/NiveshMap/config/localities.yaml) | `app.py` (line 102) | YAML Config | Yes | App blocks startup (returns missing model warning UI) |
| [data/ncr_real_estate.db](file:///c:/Users/eklav/Desktop/NiveshMap/data/ncr_real_estate.db) | `src.ncr_intelligence.database.connection` | SQLite DB | Yes | SQLite session failure on geospatial queries |
| [data/processed/forecaster.pickle](file:///c:/Users/eklav/Desktop/NiveshMap/data/processed/forecaster.pickle) | `app.py` (line 101) | Serialized Model | Yes (Force-added) | App blocks startup (returns missing model warning UI) |
| [data/processed/phase0_quarterly_panel.csv](file:///c:/Users/eklav/Desktop/NiveshMap/data/processed/phase0_quarterly_panel.csv) | `app.py` (line 118) | CSV Dataset | Yes (Force-added) | App blocks startup (returns missing model warning UI) |
| [data/processed/locality_feasibility.csv](file:///c:/Users/eklav/Desktop/NiveshMap/data/processed/locality_feasibility.csv) | `app.py` (line 119) | CSV Dataset | Yes (Force-added) | App blocks startup (returns missing model warning UI) |

---

## Path Validation

1.  **Windows/Linux Safety**: All paths are resolved using either `pathlib.Path` or `os.path.join(root, ...)` relative to the repository root directory. No absolute Windows drive paths or backslash-only strings exist in runtime loading code.
2.  **Git Check**: All seven files listed above are currently tracked and committed in the `stabilization` branch.
