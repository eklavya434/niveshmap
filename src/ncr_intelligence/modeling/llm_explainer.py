import os
from typing import Dict, Any, List

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


class StrategySuitabilityExplainer:
    """Uses Google Gemini to explain structured strategy suitability outputs."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.initialized = False

        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.initialized = True
            except Exception:
                self.initialized = False

    def generate_explanation(
        self,
        profile_summary: Dict[str, Any],
        capacity_result: Dict[str, Any],
        strategy_scores: List[Dict[str, Any]],
        top_strategy: Dict[str, Any],
        location_matches: List[Dict[str, Any]]
    ) -> str:
        """Generates natural language report explaining the strategy alignment and risks."""
        if not self.initialized:
            return self._fallback_explanation(top_strategy, strategy_scores, location_matches)

        # Format inputs for prompt
        strategy_scores_str = "\n".join([
            f"- {s['strategy']}: {s['suitability_score']}/100 ({s['suitability_band']})"
            for s in strategy_scores
        ])
        
        matches_list = []
        for m in location_matches:
            if m["match_band"] != "INSUFFICIENT_DATA" and m["match_band"] != "N/A":
                matches_list.append(
                    f"- {m['locality']} ({m['region']}): Match Score {m['match_score']}/100 ({m['match_band']}). Risks: {', '.join(m['risk_factors']) or 'None'}"
                )
        location_matches_str = "\n".join(matches_list) if matches_list else "No strategy-aligned research areas found."

        prompt = f"""
You are a Senior Geospatial & Real Estate Investment Analyst specializing in Delhi NCR investment suitability.

Explain the structured real estate strategy suitability outcomes below.

Constraints:
1. Ground your explanation STRICTLY on the provided numbers, scores, and capacity brackets.
2. DO NOT calculate or modify the scores or select a different top strategy. Explain the outputs exactly as provided.
3. DO NOT invent or promise any investment returns, prices, or infrastructure projects.
4. Use cautious analytical language. Avoid saying "guaranteed returns", "you should definitely buy", "best investment", "risk-free", or "prices will increase". Instead, use phrases like "the analysis indicates", "more aligned with your stated profile", "scenario-dependent", or "potential research candidate".

[USER PROFILE & CAPACITY SUMMARY]
Stated Goal: {profile_summary.get('primary_real_estate_goal')}
Annual Income: Rs. {profile_summary.get('annual_household_income')}
Available Capital: Rs. {profile_summary.get('available_investment_capital')}
Monthly Debt obligations: Rs. {profile_summary.get('existing_monthly_emi')}
Dependents: {profile_summary.get('number_dependents')}
Horizon: {profile_summary.get('investment_horizon')}
Risk Tolerance: {profile_summary.get('risk_tolerance')}
Liquidity requirement: {profile_summary.get('liquidity_requirement')}
Financial Capacity Class: {capacity_result.get('capacity_class')}
Debt Burden Class: {capacity_result.get('debt_burden')}

[STRATEGY SUITABILITY SCORES]
(Scores are 0-100 suitability metrics, not probability of profit or expected return.)
{strategy_scores_str}

[TOP ALIGNED STRATEGY]
Strategy: {top_strategy.get('strategy')}
Score: {top_strategy.get('suitability_score')}/100 ({top_strategy.get('suitability_band')})
Positive Factors: {', '.join(top_strategy.get('positive_factors', []))}
Negative Factors: {', '.join(top_strategy.get('negative_factors', []))}
Major Risks: {', '.join(top_strategy.get('major_risks', []))}
Data Limitations: {', '.join(top_strategy.get('data_limitations', []))}

[POTENTIAL ALIGNED NCR RESEARCH AREAS]
{location_matches_str}

Generate a professional, structured analysis explaining:
1. Why this top strategy aligns with the user's financial profile.
2. Why other strategies ranked lower (e.g. why long-term land is low if liquidity requirement is high or horizon is short).
3. What are the key risk factors and data limitations (e.g. lack of short-term resale transaction liquidity evidence) to keep in mind.

Provide a concise, 3-paragraph report.
"""
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"⚠️ **Gemini Explanation Generation Failed**: {e}\n\n{self._fallback_explanation(top_strategy, strategy_scores, location_matches)}"

    def _fallback_explanation(
        self,
        top_strategy: Dict[str, Any],
        strategy_scores: List[Dict[str, Any]],
        location_matches: List[Dict[str, Any]]
    ) -> str:
        """Engine-generated markdown explanation fallback if Gemini API is offline."""
        pos_str = "\n".join([f"- {f}" for f in top_strategy.get("positive_factors", [])])
        neg_str = "\n".join([f"- {f}" for f in top_strategy.get("negative_factors", [])])
        risk_str = "\n".join([f"- {f}" for f in top_strategy.get("major_risks", [])])
        limit_str = "\n".join([f"- {f}" for f in top_strategy.get("data_limitations", [])])

        report = f"""
### 📊 Suitability Analysis Report (Fallback)

The analysis indicates that the strategy **{top_strategy['strategy'].replace('_', ' ')}** is the most aligned with your stated profile (Suitability Score: **{top_strategy['suitability_score']}/100**, Band: **{top_strategy['suitability_band']}**).

#### Key Alignment Factors:
{pos_str or "- Stated goal and financial constraints align with this strategy."}

#### Identified Constraints & Drawbacks:
{neg_str or "- No major negative constraints identified for this strategy."}

#### Stated Strategy Risks & Data Limitations:
{risk_str or "- Standard real estate illiquidity and transaction costs apply."}
{limit_str}
"""
        return report

