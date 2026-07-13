import os
from typing import Dict, Any

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class GroundedAIExplainer:
    """Uses Google Gemini to explain scenario-conditioned forecasts with grounded context facts."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.initialized = False
        
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.initialized = True
            except Exception:
                self.initialized = False

    def generate_explanation(self, digest_data: Dict[str, Any]) -> str:
        """
        Generates a grounded natural language investment report comparing scenarios.
        Enforces strict constraints: does not predict prices itself, only explains pipeline output.
        """
        if not self.initialized:
            return (
                "⚠️ **Gemini API Explainer Offline**: Please configure the `GEMINI_API_KEY` environment variable "
                "or install the `google-generativeai` package to enable automated grounded AI explanations."
            )
            
        prompt = f"""
You are a Senior Geospatial & Real Estate Investment Analyst specializing in Delhi NCR infrastructure developments.

Explain the structured real estate forecasting pipeline outputs below.

Constraints:
1. Ground your explanation STRICTLY on the provided numbers and coordinates.
2. DO NOT fabricate or predict any property prices yourself. Only explain the outputs from the ML regressor model.
3. Keep the tone analytical, highlighting spatial-temporal project milestones (e.g. Metro completion, Airport delays) and how they influence the model's price projections.

[CONTEXT LOCALITY]
Locality: {digest_data.get('locality_name')}
Region: {digest_data.get('region')}
Maturity Class: {digest_data.get('maturity_class')}
Baseline Price: Rs. {digest_data.get('baseline_price')}/sqft

[SCENARIO A PROJECTION (High Progress)]
- Metro Stage: {digest_data.get('metro_stage_a')}
- Expressway Stage: {digest_data.get('exp_stage_a')}
- Airport Stage: {digest_data.get('airport_stage_a')}
- Projected Price in 4 Quarters: Rs. {digest_data.get('price_a')}/sqft ({digest_data.get('growth_a')}% shift)

[SCENARIO C PROJECTION (Delayed / Stalled)]
- Metro Stage: {digest_data.get('metro_stage_c')}
- Expressway Stage: {digest_data.get('exp_stage_c')}
- Airport Stage: {digest_data.get('airport_stage_c')}
- Projected Price in 4 Quarters: Rs. {digest_data.get('price_c')}/sqft ({digest_data.get('growth_c')}% shift)

[MODEL GEODISTANCES & ATTRIBUTIONS]
- Nearest Metro Distance (Scenario A): {digest_data.get('metro_dist_a')} km
- Primary Model Split Driver: {digest_data.get('primary_driver')} (contributed {digest_data.get('driver_importance')}% of tree splits)
- Price Variance between Scenario A and C: Rs. {digest_data.get('price_diff')}/sqft

Generate a concise, 3-paragraph investment summary detailing the comparison.
"""
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"⚠️ **Gemini Explanation Generation Failed**: {e}"
