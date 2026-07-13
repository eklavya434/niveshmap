import os
import yaml
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from datetime import date
import requests
import folium
from streamlit_folium import st_folium
from src.ncr_intelligence.modeling.models import ForecasterModel
from src.ncr_intelligence.modeling.forecaster import ScenarioForecaster
from src.ncr_intelligence.modeling.llm_explainer import GroundedAIExplainer

# ----------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# ----------------------------------------------------
st.set_page_config(
    page_title="NCR Real Estate Scenario Forecasting Platform",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium dark theme CSS
st.markdown("""
<style>
    /* Dark Theme Global Adjustments */
    .stApp {
        background-color: #0E1117;
        color: #E2E8F0;
    }
    
    /* Sleek metric card styling */
    .metric-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
    }
    .metric-title {
        color: #94A3B8;
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        color: #F8FAFC;
        font-size: 1.75rem;
        font-weight: 700;
        line-height: 1;
    }
    .metric-delta-plus {
        color: #34D399;
        font-size: 0.875rem;
        font-weight: 600;
        margin-top: 4px;
    }
    .metric-delta-minus {
        color: #F87171;
        font-size: 0.875rem;
        font-weight: 600;
        margin-top: 4px;
    }
    
    /* Gate badge styling */
    .badge-pass {
        background-color: #064E3B;
        color: #34D399;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .badge-fail {
        background-color: #7F1D1D;
        color: #F87171;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. HELPER FUNCTIONS & DATA LOADERS
# ----------------------------------------------------
@st.cache_resource
def load_forecaster_engine():
    model_path = "data/processed/forecaster.pickle"
    yaml_path = "config/localities.yaml"
    
    if not os.path.exists(model_path) or not os.path.exists(yaml_path):
        return None, None
        
    try:
        model = ForecasterModel.load(model_path)
        with open(yaml_path, "r", encoding="utf-8") as f:
            localities_metadata = yaml.safe_load(f)
        forecaster = ScenarioForecaster(model, localities_metadata)
        return forecaster, localities_metadata
    except Exception:
        return None, None

@st.cache_data
def load_datasets():
    panel_path = "data/processed/phase0_quarterly_panel.csv"
    feasibility_path = "data/processed/locality_feasibility.csv"
    
    if not os.path.exists(panel_path) or not os.path.exists(feasibility_path):
        return None, None
        
    try:
        panel_df = pd.read_csv(panel_path)
        feasibility_df = pd.read_csv(feasibility_path)
        return panel_df, feasibility_df
    except Exception:
        return None, None

# Project coordinates registry
PROJECT_COORDINATES = {
    "metro_stations": [
        (28.5818, 77.0592), (28.6186, 77.3719), (28.4682, 77.5147),
        (28.4664, 77.5092), (28.4554, 77.4727), (28.5996, 77.4497),
        (28.4907, 77.0984), (28.4721, 77.3168)
    ],
    "expressways": [
        (28.5300, 77.3800), (28.6100, 77.3500), (28.3000, 77.5500),
        (28.4000, 76.9800), (28.4800, 77.0800), (28.4300, 77.3300)
    ],
    "airports": [
        (28.5562, 77.1000), (28.1500, 77.5500)
    ],
    "rrts_stations": [
        (28.7061, 77.4419)
    ]
}

INFRA_METADATA = {
    (28.5818, 77.0592): {"name": "Dwarka Sector 10 Station", "type": "Metro", "details": "Operational Blue Line station serving South West Delhi."},
    (28.6186, 77.3719): {"name": "Noida Sector 62 Station", "type": "Metro", "details": "Operational Blue Line branch station serving Noida/GZB border."},
    (28.4682, 77.5147): {"name": "Omega 1 Aqua Line Station", "type": "Metro", "details": "Operational Aqua Line station in Greater Noida."},
    (28.4664, 77.5092): {"name": "Pari Chowk Station", "type": "Metro", "details": "Operational Aqua Line station at the gateway of Greater Noida."},
    (28.4554, 77.4727): {"name": "Sector 148 Aqua Line Station", "type": "Metro", "details": "Operational Aqua Line station near Noida Sector 150."},
    (28.5996, 77.4497): {"name": "Noida Extension Proposed Station", "type": "Metro", "details": "Proposed Metro corridor serving Greater Noida West."},
    (28.4907, 77.0984): {"name": "Micromax Moulsari Avenue Station", "type": "Metro", "details": "Operational Gurugram Rapid Metro station serving DLF Phase 3."},
    (28.4721, 77.3168): {"name": "Sarai Violet Line Station", "type": "Metro", "details": "Operational Violet Line station serving Faridabad Sector 37."},
    (28.5300, 77.3800): {"name": "Noida-Greater Noida Expressway", "type": "Expressway", "details": "Operational high-speed expressway corridor in Noida."},
    (28.6100, 77.3500): {"name": "Delhi-Meerut Expressway (NH-24)", "type": "Expressway", "details": "Operational 14-lane highway serving Ghaziabad/Indirapuram."},
    (28.3000, 77.5500): {"name": "Yamuna Expressway", "type": "Expressway", "details": "Operational expressway connecting Greater Noida to Agra (YEIDA zone)."},
    (28.4000, 76.9800): {"name": "Dwarka Expressway", "type": "Expressway", "details": "Recently operational high-speed expressway in Gurugram Sector 82."},
    (28.4800, 77.0800): {"name": "Delhi-Gurugram Expressway (NH-48)", "type": "Expressway", "details": "Operational highway corridor serving Gurugram cyber hub."},
    (28.4300, 77.3300): {"name": "Mathura Road (NH-2)", "type": "Expressway", "details": "Operational corridor serving Faridabad industrial zones."},
    (28.5562, 77.1000): {"name": "Indira Gandhi International Airport (IGI)", "type": "Airport", "details": "Operational international airport serving Delhi NCR."},
    (28.1500, 77.5500): {"name": "Noida International Airport (Jewar)", "type": "Airport", "details": "Under-construction international airport serving YEIDA zone."},
    (28.7061, 77.4419): {"name": "Guldhar RRTS Station", "type": "RRTS", "details": "Operational RapidX/RRTS station serving Raj Nagar Extension."}
}

def query_map_cells(min_lat, min_lon, max_lat, max_lon, quarter=None):
    url = "http://localhost:8000/api/map/cells"
    params = {
        "min_lat": str(min_lat),
        "min_lon": str(min_lon),
        "max_lat": str(max_lat),
        "max_lon": str(max_lon)
    }
    if quarter:
        params["quarter"] = quarter
    try:
        response = requests.get(url, params=params, timeout=2.0)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    
    try:
        from src.ncr_intelligence.api.dependencies import build_default_spatial_service
        service = build_default_spatial_service()
        return service.get_cells(min_lat, min_lon, max_lat, max_lon, quarter=quarter)
    except Exception:
        return {"cells": [], "returned_cells": 0}

def query_map_cell(lat, lon, quarter=None, scenario=None):
    url = "http://localhost:8000/api/map/cell"
    params = {
        "lat": str(lat),
        "lon": str(lon)
    }
    if quarter:
        params["quarter"] = quarter
    if scenario:
        params["scenario"] = scenario
    try:
        response = requests.get(url, params=params, timeout=2.0)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 422:
            return {"error": response.json().get("error", {})}
    except Exception:
        pass
        
    try:
        from src.ncr_intelligence.api.dependencies import build_default_spatial_service
        service = build_default_spatial_service()
        try:
            return service.get_cell(lat, lon, quarter=quarter, scenario=scenario)
        except Exception as exc:
            from src.ncr_intelligence.geospatial.spatial_intelligence import UnsupportedGeographyError, InvalidSpatialPointError
            if isinstance(exc, UnsupportedGeographyError):
                return {"error": {"code": "OUTSIDE_SUPPORTED_GEOGRAPHY", "message": str(exc)}}
            elif isinstance(exc, InvalidSpatialPointError):
                return {"error": {"code": "INVALID_COORDINATES", "message": str(exc)}}
            raise
    except Exception as e:
        return {"error": {"code": "SPATIAL_LAYER_ERROR", "message": str(e)}}

def add_infrastructure_markers(m, show_metro, show_rrts, show_expressway, show_airport):
    for coords, meta in INFRA_METADATA.items():
        infra_type = meta["type"]
        if infra_type == "Metro" and not show_metro:
            continue
        if infra_type == "RRTS" and not show_rrts:
            continue
        if infra_type == "Expressway" and not show_expressway:
            continue
        if infra_type == "Airport" and not show_airport:
            continue
            
        color = "blue" if infra_type == "Metro" else "purple" if infra_type == "RRTS" else "green" if infra_type == "Expressway" else "orange"
        icon_type = "info-sign" if infra_type == "Metro" else "dashboard" if infra_type == "RRTS" else "road" if infra_type == "Expressway" else "plane"
        
        popup_html = f"""
        <strong>{meta['name']}</strong><br>
        Class: {infra_type}<br>
        {meta['details']}
        """
        
        folium.Marker(
            location=[coords[0], coords[1]],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color=color, icon=icon_type),
            tooltip=meta["name"]
        ).add_to(m)

# ----------------------------------------------------
# 3. INTERFACE BUILDER
# ----------------------------------------------------
forecaster, localities_meta = load_forecaster_engine()
panel_df, feasibility_df = load_datasets()

# Block UI if models or datasets are missing
if forecaster is None or panel_df is None:
    st.title("🏢 NCR Infrastructure-Driven Real Estate Platform")
    st.warning("⚠️ Baseline datasets or serialized ML models are missing.")
    st.info("Please run the execution scripts to initialize datasets and train the ML models first:")
    st.code("python scripts/build_phase0_dataset.py\npython scripts/train_forecaster.py")
    st.stop()

# Load localities listing
localities_list = list(forecaster.localities_metadata.keys())

# Initialize session state variables for navigation and selection
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "🗺️ Explore NCR Map"
if "selected_loc_id" not in st.session_state:
    st.session_state.selected_loc_id = localities_list[0]
if "map_center" not in st.session_state:
    st.session_state.map_center = [28.5, 77.3]
if "map_zoom" not in st.session_state:
    st.session_state.map_zoom = 10

# Main navigation in the sidebar
with st.sidebar:
    st.title("🏢 NiveshMap Platform")
    app_mode = st.selectbox(
        "Navigation Mode",
        options=["🗺️ Explore NCR Map", "🔍 Scenario Analyzer"],
        index=0 if st.session_state.app_mode == "🗺️ Explore NCR Map" else 1
    )
    st.session_state.app_mode = app_mode

if st.session_state.app_mode == "🗺️ Explore NCR Map":
    st.subheader("Interactive Delhi NCR Intelligence Map")
    
    with st.sidebar:
        st.divider()
        st.subheader("Map Options")
        
        # Locality search functionality
        search_options = ["None"] + localities_list
        search_loc_id = st.selectbox(
            "Search Locality on Map",
            options=search_options,
            format_func=lambda x: "Select Locality..." if x == "None" else f"{forecaster.localities_metadata[x]['locality_name']} ({forecaster.localities_metadata[x]['region']})"
        )
        
        # Layer controls
        st.subheader("Infrastructure Layers")
        show_metro = st.checkbox("Metro Stations", value=True)
        show_rrts = st.checkbox("RRTS Stations", value=True)
        show_expressways = st.checkbox("Expressway reference points", value=True)
        show_airports = st.checkbox("Airport reference points", value=True)
        
        st.divider()
        st.info("💡 **NiveshMap Disclaimer**\n\nNiveshMap provides zone/locality-level analytical intelligence based on available source data. It does not provide parcel-level property valuation or investment advice.")

    # Two column layout: Left (Map), Right (Click to Analyze panel)
    map_col, details_col = st.columns([7, 5])
    
    with map_col:
        # Update map center and trigger cell loading if search is selected
        if search_loc_id != "None":
            loc_meta = forecaster.localities_metadata[search_loc_id]
            st.session_state.map_center = [loc_meta["latitude"], loc_meta["longitude"]]
            st.session_state.map_zoom = 12
            st.session_state.selected_cell_data = query_map_cell(loc_meta["latitude"], loc_meta["longitude"])
            st.session_state.selected_loc_id = search_loc_id
            
        m = folium.Map(
            location=st.session_state.map_center,
            zoom_start=st.session_state.map_zoom,
            tiles="CartoDB dark_matter"
        )
        
        # Viewport coordinates query
        if "viewport_bounds" in st.session_state:
            v = st.session_state.viewport_bounds
            cells_data = query_map_cells(v["min_lat"], v["min_lon"], v["max_lat"], v["max_lon"])
        else:
            cells_data = query_map_cells(28.1, 76.8, 28.8, 77.6)
            
        # Add cells GeoJSON layer
        for cell in cells_data.get("cells", []):
            geom = cell["cell"]["geometry"]
            readiness = cell["cell"]["spatial_readiness"]
            h3_index = cell["cell"]["h3_index"]
            
            if readiness == "LOCALITY_ANCHORED_ONLY":
                color = "#3b82f6"  # Blue
                fill_opacity = 0.4
            elif readiness == "INFRASTRUCTURE_INTELLIGENCE_ONLY":
                color = "#94a3b8"  # Grey
                fill_opacity = 0.2
            else:
                color = "#475569"  # Dark Grey
                fill_opacity = 0.1
                
            folium.GeoJson(
                geom,
                style_function=lambda x, color=color, fill_opacity=fill_opacity: {
                    "fillColor": color,
                    "color": color,
                    "weight": 1.5,
                    "fillOpacity": fill_opacity
                },
                tooltip=f"H3 Index: {h3_index} ({readiness})"
            ).add_to(m)
            
        # Draw layers
        add_infrastructure_markers(m, show_metro, show_rrts, show_expressways, show_airports)
        
        st_map = st_folium(m, width="100%", height=550, key="ncr_leaflet_map")
        
        if st_map:
            new_bounds = st_map.get("bounds")
            if new_bounds:
                st.session_state.viewport_bounds = {
                    "min_lat": new_bounds["_southWest"]["lat"],
                    "min_lon": new_bounds["_southWest"]["lng"],
                    "max_lat": new_bounds["_northEast"]["lat"],
                    "max_lon": new_bounds["_northEast"]["lng"]
                }
                
            last_clicked = st_map.get("last_clicked")
            if last_clicked:
                click_lat = last_clicked["lat"]
                click_lon = last_clicked["lng"]
                if "prev_clicked" not in st.session_state or st.session_state.prev_clicked != last_clicked:
                    st.session_state.prev_clicked = last_clicked
                    st.session_state.selected_cell_data = query_map_cell(click_lat, click_lon)
                    cell_info = st.session_state.selected_cell_data
                    if "locality" in cell_info and cell_info["locality"].get("locality_id"):
                        st.session_state.selected_loc_id = cell_info["locality"]["locality_id"]

    with details_col:
        st.subheader("🎯 Click to Analyze")
        cell_info = st.session_state.get("selected_cell_data")
        
        if not cell_info:
            st.info("Click on any H3 zone or marker to analyze price, infrastructure, and analytical readiness.")
        elif "error" in cell_info:
            err = cell_info["error"]
            if err.get("code") == "OUTSIDE_SUPPORTED_GEOGRAPHY":
                st.warning("Outside Supported Geography")
                st.write("This location is outside the NiveshMap locality-centroid coverage buffers.")
            else:
                st.error(f"Error ({err.get('code')}): {err.get('message')}")
        else:
            # Location
            st.markdown("### 🗺️ Location Details")
            loc = cell_info.get("locality", {})
            st.write(f"**Locality Name**: {loc.get('name') or 'Unassigned'}")
            st.write(f"**Region**: {loc.get('region') or 'Unassigned'}")
            st.write(f"**H3 Cell Index**: `{cell_info['cell']['h3_index']}`")
            
            # Price Intelligence
            st.markdown("### 💰 Price Intelligence")
            price = cell_info.get("price_intelligence", {})
            val = price.get("value")
            est_type = price.get("estimate_type")
            
            if val is not None:
                st.success(f"₹ {val:,.2f} {price.get('unit', 'INR_PER_SQFT')}")
                st.write(f"**Estimate Type**: `{est_type}`")
                st.write(f"**Signal Type**: `{price.get('price_signal_type')}`")
                st.write(f"**As-of Quarter**: `{price.get('as_of_quarter')}`")
                st.caption("*Locality-level price signal — not a parcel or cell valuation.*")
            else:
                st.warning("Spatial price estimate unavailable")
                st.caption(f"Reason: {', '.join(cell_info['data_quality'].get('limitations', [])) or 'No data found'}")
                
            # Infrastructure Proximity
            st.markdown("### 🚆 Infrastructure Proximity")
            infra = cell_info.get("infrastructure", {})
            m_op = infra.get("nearest_operational_metro_km")
            m_pr = infra.get("nearest_proposed_metro_km")
            rrt = infra.get("nearest_rrts_km")
            exp = infra.get("nearest_expressway_highway_km")
            arp = infra.get("airport_distance_km")

            st.write(f"**Nearest Operational Metro**: {m_op:.2f} km" if m_op is not None else "**Nearest Operational Metro**: Unavailable")
            st.write(f"**Nearest Proposed Metro**: {m_pr:.2f} km" if m_pr is not None else "**Nearest Proposed Metro**: Unavailable")
            st.write(f"**Nearest RRTS Station**: {rrt:.2f} km" if rrt is not None else "**Nearest RRTS Station**: Unavailable")
            st.write(f"**Nearest Expressway/Highway**: {exp:.2f} km" if exp is not None else "**Nearest Expressway/Highway**: Unavailable")
            st.write(f"**Airport Distance**: {arp:.2f} km" if arp is not None else "**Airport Distance**: Unavailable")
            
            # Analytical Readiness
            st.markdown("### 📊 Analytical Readiness")
            spatial_readiness = cell_info["cell"]["spatial_readiness"]
            
            data_readiness = None
            data_class = None
            if loc.get("locality_id"):
                loc_readiness = feasibility_df[feasibility_df["locality_id"] == loc.get("locality_id")]
                if not loc_readiness.empty:
                    data_readiness = loc_readiness.iloc[0]["data_readiness_score"]
                    data_class = loc_readiness.iloc[0]["readiness_class"]
                    
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                st.write("**Data Readiness**")
                if data_readiness is not None:
                    st.write(f"Score: `{data_readiness} / 100`")
                    st.write(f"Class: `{data_class}`")
                else:
                    st.write("Score: `N/A`")
                st.caption("Data Readiness evaluates the depth, source quality, and timeline reconstruction completeness at the locality level.")
            with r_col2:
                st.write("**Spatial Readiness**")
                st.write(f"Category: `{spatial_readiness}`")
                st.caption("Spatial Readiness evaluates fallback assignment distance, coordinate source quality, and spatial pricing model availability.")
                
            # Limitations
            st.markdown("### ⚠️ Data Limitations")
            lims = cell_info["data_quality"].get("limitations", [])
            if lims:
                for l in lims:
                    st.write(f"- {l}")
            else:
                st.write("No major spatial limitations reported.")
                
            # Historical trend chart
            if loc.get("locality_id"):
                loc_hist = panel_df[panel_df["locality_id"] == loc.get("locality_id")].sort_values("quarter")
                if not loc_hist.empty:
                    st.markdown("### 📈 Historical Price Trend")
                    fig_hist = go.Figure()
                    fig_hist.add_trace(go.Scatter(
                        x=loc_hist["quarter"],
                        y=loc_hist["price_proxy"],
                        mode="lines+markers",
                        name="Trend",
                        line=dict(color="#3b82f6", width=2)
                    ))
                    fig_hist.update_layout(
                        margin=dict(l=20, r=20, t=20, b=20),
                        height=200,
                        template="plotly_dark",
                        xaxis_title="Quarter",
                        yaxis_title="INR/sqft",
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
                    
            # Scenario Navigation
            if loc.get("locality_id"):
                st.markdown("---")
                if st.button("Explore Scenarios"):
                    st.session_state.selected_loc_id = loc.get("locality_id")
                    st.session_state.app_mode = "🔍 Scenario Analyzer"
                    st.rerun()

elif st.session_state.app_mode == "🔍 Scenario Analyzer":
    # ----------------------------------------------------
    # 4. SIDEBAR SELECTION & SCENARIOS CONFIG
    # ----------------------------------------------------
    with st.sidebar:
        st.subheader("Scenario Options")
        
        # 1. Target Locality dropdown
        selected_loc_id = st.selectbox(
            "Select Target Locality",
            options=localities_list,
            index=localities_list.index(st.session_state.selected_loc_id),
            format_func=lambda x: f"{forecaster.localities_metadata[x]['locality_name']} ({forecaster.localities_metadata[x]['region']})"
        )
        st.session_state.selected_loc_id = selected_loc_id
        selected_loc = forecaster.localities_metadata[selected_loc_id]
        
        st.divider()
        
        # Stages taxonomy selector options
        stages_options = ["NONE", "PROPOSED", "APPROVED", "CONTRACTED", "UNDER_CONSTRUCTION", "OPERATIONAL", "STALLED_DELAYED_CANCELLED"]
        
        # 2. Scenario A controls
        st.subheader("🟢 Scenario A (High Progress)")
        metro_a = st.selectbox("Metro Stage A", options=stages_options, index=5, key="metro_a") # OPERATIONAL
        exp_a = st.selectbox("Expressway Stage A", options=stages_options, index=5, key="exp_a")     # OPERATIONAL
        airport_a = st.selectbox("Airport Stage A", options=stages_options, index=4, key="airport_a") # UNDER_CONSTRUCTION
        rrts_a = st.selectbox("RRTS Stage A", options=stages_options, index=0, key="rrts_a")         # NONE
        
        st.divider()
        
        # 3. Scenario B controls
        st.subheader("🔵 Scenario B (Baseline / Proposed)")
        metro_b = st.selectbox("Metro Stage B", options=stages_options, index=1, key="metro_b") # PROPOSED
        exp_b = st.selectbox("Expressway Stage B", options=stages_options, index=5, key="exp_b")     # OPERATIONAL
        airport_b = st.selectbox("Airport Stage B", options=stages_options, index=4, key="airport_b") # UNDER_CONSTRUCTION
        rrts_b = st.selectbox("RRTS Stage B", options=stages_options, index=0, key="rrts_b")         # NONE
        
        st.divider()
        
        # 4. Scenario C controls
        st.subheader("🟠 Scenario C (Delayed / Stalled)")
        metro_c = st.selectbox("Metro Stage C", options=stages_options, index=1, key="metro_c") # PROPOSED
        exp_c = st.selectbox("Expressway Stage C", options=stages_options, index=5, key="exp_c")     # OPERATIONAL
        airport_c = st.selectbox("Airport Stage C", options=stages_options, index=6, key="airport_c") # STALLED_DELAYED_CANCELLED
        rrts_c = st.selectbox("RRTS Stage C", options=stages_options, index=0, key="rrts_c")         # NONE
        
        st.divider()
        st.info("💡 **NiveshMap Disclaimer**\n\nNiveshMap provides zone/locality-level analytical intelligence based on available source data. It does not provide parcel-level property valuation or investment advice.")

    # ----------------------------------------------------
    # 5. DYNAMIC SCENARIO PROJECTIONS
    # ----------------------------------------------------
    # Get latest historical row to serve as baseline
    loc_history = panel_df[panel_df["locality_id"] == st.session_state.selected_loc_id].sort_values("quarter")
    latest_hist_row = loc_history.iloc[-1].to_dict()
    selected_loc = forecaster.localities_metadata[st.session_state.selected_loc_id]

    # Calculate forecasts
    forecast_a = forecaster.forecast_scenario(st.session_state.selected_loc_id, metro_a, exp_a, airport_a, rrts_a, n_quarters=4, latest_row=latest_hist_row)
    forecast_b = forecaster.forecast_scenario(st.session_state.selected_loc_id, metro_b, exp_b, airport_b, rrts_b, n_quarters=4, latest_row=latest_hist_row)
    forecast_c = forecaster.forecast_scenario(st.session_state.selected_loc_id, metro_c, exp_c, airport_c, rrts_c, n_quarters=4, latest_row=latest_hist_row)

    # Get feasibility metadata
    readiness_row = feasibility_df[feasibility_df["locality_id"] == st.session_state.selected_loc_id].iloc[0].to_dict()

    # ----------------------------------------------------
    # 6. MAIN CONTENT LAYOUT
    # ----------------------------------------------------
    st.title(f"🏢 Real Estate Intelligence: {selected_loc['locality_name']}")
    st.caption(f"NCR region: **{selected_loc['region']}** | District: **{selected_loc['district']}** | Maturity Class: **{selected_loc['urban_maturity_class']}**")

    # Top overview cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Data Readiness Score</div>
            <div class="metric-value">{readiness_row['data_readiness_score']} / 100</div>
            <div class="metric-delta-plus">Class: {readiness_row['readiness_class'].replace('_', ' ')}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Latest Price Proxy</div>
            <div class="metric-value">₹ {latest_hist_row['price_proxy']:.0f}</div>
            <div class="metric-delta-plus">INR/sqft (as of {latest_hist_row['quarter']})</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        # Estimate forecast trajectory under high progression
        final_a = forecast_a[-1]["forecasted_price_proxy"]
        growth_pct = ((final_a - latest_hist_row['price_proxy']) / latest_hist_row['price_proxy']) * 100
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Scenario A Proj. Growth</div>
            <div class="metric-value">₹ {final_a:.0f}</div>
            <div class="metric-delta-plus">+{growth_pct:.2f}% (over 4 quarters)</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        # Trajectory under stalled/delayed scenario
        final_c = forecast_c[-1]["forecasted_price_proxy"]
        growth_c = ((final_c - latest_hist_row['price_proxy']) / latest_hist_row['price_proxy']) * 100
        delta_class = "metric-delta-minus" if growth_c < 0 else "metric-delta-plus"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Scenario C Proj. Growth</div>
            <div class="metric-value">₹ {final_c:.0f}</div>
            <div class="metric-delta-plus">{growth_c:+.2f}% (over 4 quarters)</div>
        </div>
        """, unsafe_allow_html=True)

    # Main Tab navigation
    t1, t2, t3, t4 = st.tabs([
        "📈 Scenario Forecast Planner", 
        "📊 Data Readiness Audit", 
        "🗺️ Proximity & Buffer Insights", 
        "🧠 Grounded Explainability (XAI)"
    ])

    # ----------------------------------------------------
    # TAB 1: SCENARIO FORECAST PLANNER
    # ----------------------------------------------------
    with t1:
        st.subheader("Interactive What-If Scenario Comparison")
        
        # Check eligibility first
        is_eligible = readiness_row["readiness_class"] in {"FULL_FORECAST_ELIGIBLE", "LIMITED_FORECAST_ELIGIBLE"}
        
        if not is_eligible:
            st.warning(f"⚠️ **Forecasting Disabled**: This locality has been classified as **{readiness_row['readiness_class'].replace('_', ' ')}**.")
            st.info("The scenario forecaster requires at least 12 quarters of price observations and reconstructable infrastructure event history. Please refer to Tab 2 to audit data completeness.")
        
        # Plotly lines chart
        fig = go.Figure()
        
        # Historical path
        fig.add_trace(go.Scatter(
            x=loc_history["quarter"],
            y=loc_history["price_proxy"],
            mode="lines+markers",
            name="Historical Price Proxy",
            line=dict(color="#94A3B8", width=3)
        ))
        
        if is_eligible:
            # Forecast A
            forecast_qtrs = [row["quarter"] for row in forecast_a]
            # Attach last historical point to make chart continuous
            chart_qtrs = [latest_hist_row["quarter"]] + forecast_qtrs
            
            y_a = [latest_hist_row["price_proxy"]] + [row["forecasted_price_proxy"] for row in forecast_a]
            y_b = [latest_hist_row["price_proxy"]] + [row["forecasted_price_proxy"] for row in forecast_b]
            y_c = [latest_hist_row["price_proxy"]] + [row["forecasted_price_proxy"] for row in forecast_c]
            
            fig.add_trace(go.Scatter(
                x=chart_qtrs, y=y_a, mode="lines+markers", name="Scenario A (High Progress)",
                line=dict(color="#10B981", width=3, dash="dash")
            ))
            fig.add_trace(go.Scatter(
                x=chart_qtrs, y=y_b, mode="lines+markers", name="Scenario B (Baseline)",
                line=dict(color="#3B82F6", width=3, dash="dash")
            ))
            fig.add_trace(go.Scatter(
                x=chart_qtrs, y=y_c, mode="lines+markers", name="Scenario C (Stalled/Delayed)",
                line=dict(color="#F59E0B", width=3, dash="dash")
            ))
            
        fig.update_layout(
            title="Residential Real Estate Projections vs. Transit Stage Milestones",
            xaxis_title="Quarter",
            yaxis_title="Composite Rate (INR/sqft)",
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)

    # ----------------------------------------------------
    # TAB 2: DATA READINESS AUDIT
    # ----------------------------------------------------
    with t2:
        st.subheader("Data Completeness & Analytical Gates Audit")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### Dynamic Readiness Dimension Scores")
            
            # Load details from feasibility file
            st.write(f"**Overall Score**: `{readiness_row['data_readiness_score']} / 100`")
            
            # Create progress bars for dimensions
            st.write("Historical price quarters coverage:")
            st.progress(int(min(100, (readiness_row["historical_quarters_available"] / 28) * 100)))
            
            st.write("Price source quality index:")
            st.progress(int(readiness_row["price_source_quality"]))
            
            st.write("Infrastructure timeline events depth:")
            st.progress(int(min(100, (readiness_row["infrastructure_events_found"] / 5) * 100)))
            
            st.write("Geospatial completeness:")
            st.progress(100 if readiness_row["geospatial_completeness"] == "YES" else 0)
            
        with col_b:
            st.markdown("#### Hard Gates Evaluation")
            
            # Evaluate hard gates
            has_provenance = readiness_row["price_source_quality"] > 50
            has_depth = readiness_row["historical_quarters_available"] >= 12
            has_infra = readiness_row["infrastructure_events_found"] >= 1
            
            st.markdown(f"""
            - **Price Provenance Verification**: {"<span class='badge-pass'>PASS</span>" if has_provenance else "<span class='badge-fail'>FAIL</span>"}
            - **Minimum Observations Depth (>=12 Qtrs)**: {"<span class='badge-pass'>PASS</span>" if has_depth else "<span class='badge-fail'>FAIL</span>"}
            - **Temporal Transit Reconstruction (>=1 Event)**: {"<span class='badge-pass'>PASS</span>" if has_infra else "<span class='badge-fail'>FAIL</span>"}
            """, unsafe_allow_html=True)
            
            if readiness_row["failure_reasons"]:
                st.error(f"**Failed Gate Reasons**: {readiness_row['failure_reasons']}")
            else:
                st.success("✅ Locality passed all mandatory analytical gates for forecasting.")

    # ----------------------------------------------------
    # TAB 3: PROXIMITY & BUFFER INSIGHTS
    # ----------------------------------------------------
    with t3:
        st.subheader("Centroid Proximity to Active Infrastructure Corridors")
        
        col_x, col_y = st.columns(2)
        with col_x:
            st.markdown("#### Geodesic (Haversine) Distance Measurements")
            
            st.table(pd.DataFrame({
                "Target Infrastructure": ["Nearest Metro Station (Operational)", "Nearest Proposed Metro Station", "Nearest Expressway Corridor", "Airport Terminal (IGI / Jewar)", "Nearest RRTS Station"],
                "Calculated Distance (km)": [
                    f"{latest_hist_row['distance_nearest_operational_metro_km']:.2f} km",
                    f"{latest_hist_row['distance_nearest_proposed_metro_km']:.2f} km",
                    f"{latest_hist_row['distance_nearest_expressway_km']:.2f} km",
                    f"{latest_hist_row['distance_airport_km']:.2f} km",
                    f"{latest_hist_row['distance_rrts_station_km']:.2f} km"
                ]
            }))
            
        with col_y:
            st.markdown("#### Buffer Densities (Transit Proximity Overlay)")
            st.write("Count of active transit hubs within geodesic buffers from locality centroid:")
            
            st.metric("Transit Hubs within 3km", value=int(latest_hist_row["infra_count_3km"]))
            st.metric("Transit Hubs within 5km", value=int(latest_hist_row["infra_count_5km"]))
            st.metric("Transit Hubs within 10km", value=int(latest_hist_row["infra_count_10km"]))

    # ----------------------------------------------------
    # TAB 4: EXPLAINABLE AI (XAI)
    # ----------------------------------------------------
    with t4:
        st.subheader("Explainable AI (RandomForest Feature Importances)")
        
        importances = forecaster.model.get_feature_importances()
        imp_df = pd.DataFrame({
            "Feature": list(importances.keys()),
            "Importance (%)": [v * 100 for v in importances.values()]
        }).sort_values("Importance (%)", ascending=True)
        
        # Plot feature importances in horizontal bar chart
        fig_imp = go.Figure(go.Bar(
            x=imp_df["Importance (%)"],
            y=imp_df["Feature"],
            orientation="h",
            marker=dict(color="#10B981")
        ))
        fig_imp.update_layout(
            title="Predictive Signal Contribution Matrix",
            xaxis_title="Importance Weight (%)",
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_imp, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Grounded Scenario Explanation (Digest for LLM explanation)")
        
        st.info("The text digest below represents the structured inputs fed into the Grounded AI explanation module. It summarizes the statistical shifts between Scenario A and Scenario C:")
        
        price_diff = final_a - final_c
        spatial_feats = forecaster.simulate_spatial_features(
            st.session_state.selected_loc_id, metro_a, exp_a, airport_a, rrts_a
        )
        
        digest_data = {
            "locality_name": selected_loc['locality_name'],
            "region": selected_loc['region'],
            "maturity_class": selected_loc['urban_maturity_class'],
            "baseline_price": f"{latest_hist_row['price_proxy']:.0f}",
            "metro_stage_a": metro_a,
            "exp_stage_a": exp_a,
            "airport_stage_a": airport_a,
            "price_a": f"{final_a:.0f}",
            "growth_a": f"{growth_pct:+.2f}",
            "metro_stage_c": metro_c,
            "exp_stage_c": exp_c,
            "airport_stage_c": airport_c,
            "price_c": f"{final_c:.0f}",
            "growth_c": f"{growth_c:+.2f}",
            "metro_dist_a": f"{spatial_feats['distance_nearest_operational_metro_km']:.2f}",
            "primary_driver": imp_df.iloc[-1]['Feature'],
            "driver_importance": f"{imp_df.iloc[-1]['Importance (%)']:.2f}",
            "price_diff": f"{price_diff:.2f}"
        }
        
        # Render prompt digest inside expander
        with st.expander("Show Raw Structured Prompt Digest"):
            st.code(f"""
[CONTEXT LOCALITY] {digest_data['locality_name']} ({digest_data['region']})
[BASELINE PRICE] ₹ {digest_data['baseline_price']} / sqft

[SCENARIO A PROJECTION]
- Metro: {digest_data['metro_stage_a']} | Expressway: {digest_data['exp_stage_a']} | Airport: {digest_data['airport_stage_a']}
- Projected Price (4 Quarters): ₹ {digest_data['price_a']} / sqft ({digest_data['growth_a']}% shift)

[SCENARIO C PROJECTION]
- Metro: {digest_data['metro_stage_c']} | Expressway: {digest_data['exp_stage_c']} | Airport: {digest_data['airport_stage_c']}
- Projected Price (4 Quarters): ₹ {digest_data['price_c']} / sqft ({digest_data['growth_c']}% shift)

[MODEL ATTRIBUTION]
- Proximity gap: Scenario A metro operational distance is {digest_data['metro_dist_a']} km.
- Primary feature driver: {digest_data['primary_driver']} contributed {digest_data['driver_importance']}% to the tree splits.
- Variance outcome: Scenario A leads Scenario C by ₹ {digest_data['price_diff']} / sqft.
            """)
            
        st.markdown("#### Live AI Scenario Report")
        explainer = GroundedAIExplainer()
        report = explainer.generate_explanation(digest_data)
        st.markdown(report)

