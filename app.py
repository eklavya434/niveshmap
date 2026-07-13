import os
import yaml
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from datetime import date
from src.ncr_intelligence.modeling.models import ForecasterModel
from src.ncr_intelligence.modeling.forecaster import ScenarioForecaster

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

# ----------------------------------------------------
# 4. SIDEBAR SELECTION & SCENARIOS CONFIG
# ----------------------------------------------------
with st.sidebar:
    st.title("🏢 Scenario Planner")
    
    # 1. Target Locality dropdown
    selected_loc_id = st.selectbox(
        "Select Target Locality",
        options=localities_list,
        format_func=lambda x: f"{forecaster.localities_metadata[x]['locality_name']} ({forecaster.localities_metadata[x]['region']})"
    )
    
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

# ----------------------------------------------------
# 5. DYNAMIC SCENARIO PROJECTIONS
# ----------------------------------------------------
# Get latest historical row to serve as baseline
loc_history = panel_df[panel_df["locality_id"] == selected_loc_id].sort_values("quarter")
latest_hist_row = loc_history.iloc[-1].to_dict()

# Calculate forecasts
forecast_a = forecaster.forecast_scenario(selected_loc_id, metro_a, exp_a, airport_a, rrts_a, n_quarters=4, latest_row=latest_hist_row)
forecast_b = forecaster.forecast_scenario(selected_loc_id, metro_b, exp_b, airport_b, rrts_b, n_quarters=4, latest_row=latest_hist_row)
forecast_c = forecaster.forecast_scenario(selected_loc_id, metro_c, exp_c, airport_c, rrts_c, n_quarters=4, latest_row=latest_hist_row)

# Get feasibility metadata
readiness_row = feasibility_df[feasibility_df["locality_id"] == selected_loc_id].iloc[0].to_dict()

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
        <div class="{delta_class}">{growth_c:+.2f}% (over 4 quarters)</div>
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
    
    # Generate structured prompts/explanations for potential LLM ingestion
    st.info("The text digest below represents the structured inputs fed into the Grounded AI explanation module. It summarizes the statistical shifts between Scenario A and Scenario C:")
    
    price_diff = final_a - final_c
    spatial_feats = forecaster.simulate_spatial_features(
        selected_loc_id, metro_a, exp_a, airport_a, rrts_a
    )
    st.code(f"""
[CONTEXT LOCALITY] {selected_loc['locality_name']} ({selected_loc['region']})
[BASELINE PRICE] ₹ {latest_hist_row['price_proxy']:.0f} / sqft

[SCENARIO A PROJECTION]
- Metro: {metro_a} | Expressway: {exp_a} | Airport: {airport_a}
- Projected Price (4 Quarters): ₹ {final_a:.0f} / sqft ({growth_pct:+.2f}% shift)

[SCENARIO C PROJECTION]
- Metro: {metro_c} | Expressway: {exp_c} | Airport: {airport_c}
- Projected Price (4 Quarters): ₹ {final_c:.0f} / sqft ({growth_c:+.2f}% shift)

[MODEL ATTRIBUTION]
- Proximity gap: Scenario A metro operational distance is {spatial_feats['distance_nearest_operational_metro_km']:.2f} km.
- Primary feature driver: {imp_df.iloc[-1]['Feature']} contributed {imp_df.iloc[-1]['Importance (%)']:.2f}% to the tree splits.
- Variance outcome: Scenario A leads Scenario C by ₹ {price_diff:.2f} / sqft.
    """)
