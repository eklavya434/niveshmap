"""Suitability calculation engines for Nivesh Profile and strategy matching."""

import os
from typing import Dict, Any, List, Optional
import yaml

def load_suitability_config() -> Dict[str, Any]:
    """Load configuration from config/suitability.yaml."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    path = os.path.join(root, "config", "suitability.yaml")
    if not os.path.exists(path):
        path = "config/suitability.yaml"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        # Fallback default configuration if file is missing
        return {
            "capacity": {
                "debt_burden_low": 0.20,
                "debt_burden_high": 0.45,
                "capital_brackets": {
                    "constrained": 1500000.0,
                    "limited": 4000000.0,
                    "moderate": 8000000.0,
                    "strong": 15000000.0,
                    "very_strong": 30000000.0
                }
            },
            "scoring_weights": {
                "goal_alignment_bonus": 35,
                "no_home_bonus_for_home_purchase": 25,
                "liquidity_penalty_on_land": 45,
                "short_horizon_penalty_on_land": 50,
                "high_debt_penalty_on_home_purchase": 40,
                "short_horizon_penalty_on_home": 30
            },
            "location_matching": {
                "land_appreciation": {
                    "data_readiness_weight": 0.3,
                    "scenario_upside_weight": 0.4,
                    "infra_proximity_weight": 0.3
                },
                "rental_flat": {
                    "connectivity_weight": 0.5,
                    "data_readiness_weight": 0.3,
                    "maturity_weight": 0.2
                }
            }
        }

class NiveshProfile:
    """Represents a validated user financial and investment profile."""
    
    VALID_OCCUPATIONS = {
        "SALARIED_PRIVATE", "SALARIED_GOVERNMENT", "SELF_EMPLOYED",
        "BUSINESS_OWNER", "FREELANCER", "RETIRED", "OTHER"
    }
    VALID_HOME_OWNERSHIP = {"OWNS_HOME", "DOES_NOT_OWN_HOME", "FAMILY_HOME_OR_OTHER"}
    VALID_HORIZONS = {"LESS_THAN_3_YEARS", "3_TO_5_YEARS", "5_TO_10_YEARS", "MORE_THAN_10_YEARS"}
    VALID_RISKS = {"LOW", "MODERATE", "HIGH"}
    VALID_LIQUIDITIES = {"LOW", "MODERATE", "HIGH"}
    VALID_GOALS = {"BUY_HOME_TO_LIVE", "RENTAL_INCOME", "LONG_TERM_APPRECIATION", "BUY_AND_RESELL", "UNSURE"}

    def __init__(self, data: Dict[str, Any]):
        self.occupation = data.get("occupation", "OTHER")
        if self.occupation not in self.VALID_OCCUPATIONS:
            raise ValueError(f"Invalid occupation: {self.occupation}")

        # Numeric validations
        try:
            self.annual_income = float(data["annual_household_income"])
            self.available_capital = float(data["available_investment_capital"])
            self.monthly_debt = float(data["existing_monthly_emi"])
            self.dependents = int(data["number_dependents"])
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError("annual_household_income, available_investment_capital, and existing_monthly_emi must be numeric; number_dependents must be an integer.") from exc

        if self.annual_income < 0 or self.available_capital < 0 or self.monthly_debt < 0 or self.dependents < 0:
            raise ValueError("Financial values and dependents cannot be negative.")

        self.home_ownership = data.get("current_home_ownership", "FAMILY_HOME_OR_OTHER")
        if self.home_ownership not in self.VALID_HOME_OWNERSHIP:
            raise ValueError(f"Invalid home ownership: {self.home_ownership}")

        self.horizon = data.get("investment_horizon", "3_TO_5_YEARS")
        if self.horizon not in self.VALID_HORIZONS:
            raise ValueError(f"Invalid investment horizon: {self.horizon}")

        self.risk_tolerance = data.get("risk_tolerance", "MODERATE")
        if self.risk_tolerance not in self.VALID_RISKS:
            raise ValueError(f"Invalid risk tolerance: {self.risk_tolerance}")

        self.liquidity_requirement = data.get("liquidity_requirement", "MODERATE")
        if self.liquidity_requirement not in self.VALID_LIQUIDITIES:
            raise ValueError(f"Invalid liquidity requirement: {self.liquidity_requirement}")

        self.primary_goal = data.get("primary_real_estate_goal", "UNSURE")
        if self.primary_goal not in self.VALID_GOALS:
            raise ValueError(f"Invalid primary goal: {self.primary_goal}")


class FinancialCapacityEngine:
    """Evaluates and derives capacity parameters from a NiveshProfile."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or load_suitability_config()

    def evaluate(self, profile: NiveshProfile) -> Dict[str, Any]:
        monthly_income = profile.annual_income / 12.0
        
        # Safe debt burden ratio handling zero income
        if monthly_income > 0:
            debt_burden_ratio = profile.monthly_debt / monthly_income
        else:
            debt_burden_ratio = 1.0 if profile.monthly_debt > 0 else 0.0

        # Capital to income ratio
        if profile.annual_income > 0:
            capital_to_income_ratio = profile.available_capital / profile.annual_income
        else:
            capital_to_income_ratio = 0.0

        # Dependent load logic
        dependent_load = "HIGH" if profile.dependents >= 3 else "MODERATE" if profile.dependents >= 1 else "LOW"

        # Determine financial capacity class based on capital brackets and debt load
        brackets = self.config["capacity"]["capital_brackets"]
        debt_low = self.config["capacity"]["debt_burden_low"]
        debt_high = self.config["capacity"]["debt_burden_high"]

        capital = profile.available_capital
        
        # Capital-strength categorization
        if capital < brackets["constrained"]:
            base_class = "CONSTRAINED"
        elif capital < brackets["limited"]:
            base_class = "LIMITED"
        elif capital < brackets["moderate"]:
            base_class = "MODERATE"
        elif capital < brackets["strong"]:
            base_class = "STRONG"
        else:
            base_class = "VERY_STRONG"

        # Adjust capacity class based on debt burden
        classes = ["CONSTRAINED", "LIMITED", "MODERATE", "STRONG", "VERY_STRONG"]
        idx = classes.index(base_class)
        
        if base_class != "CONSTRAINED":
            if debt_burden_ratio > debt_high:
                # Downgrade one step
                idx = max(1, idx - 1)
            elif debt_burden_ratio < debt_low:
                # Upgrade one step
                idx = min(len(classes) - 1, idx + 1)

        capacity_class = classes[idx]

        return {
            "capacity_class": capacity_class,
            "monthly_income": monthly_income,
            "debt_burden_ratio": debt_burden_ratio,
            "debt_burden": "HIGH" if debt_burden_ratio > debt_high else "LOW" if debt_burden_ratio < debt_low else "MODERATE",
            "capital_strength": base_class,
            "capital_to_income_ratio": capital_to_income_ratio,
            "dependent_load": dependent_load,
            "horizon": profile.horizon,
            "liquidity_pressure": profile.liquidity_requirement,
            "risk_tolerance": profile.risk_tolerance,
            "home_ownership_context": profile.home_ownership,
            "goal": profile.primary_goal
        }


class StrategySuitabilityEngine:
    """Calculates suitability scores and bands for real-estate strategies."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or load_suitability_config()

    def calculate(self, profile: NiveshProfile, capacity: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        weights = self.config["scoring_weights"]

        # Strategy 1: WAIT_AND_ACCUMULATE_CAPITAL
        wait_score = 30
        wait_pos = []
        wait_neg = []
        wait_risks = []
        wait_limits = []

        if capacity["capacity_class"] == "CONSTRAINED":
            wait_score += 60
            wait_pos.append("Highly suited due to severely constrained current investment capital.")
        elif capacity["capacity_class"] == "LIMITED":
            wait_score += 45
            wait_pos.append("Suited due to limited capital resources for outright property acquisition.")
        else:
            wait_neg.append("Capital levels are strong enough to support direct property investment.")

        if profile.primary_goal == "UNSURE":
            wait_score += 15
            wait_pos.append("Recommended while investment goals are still being finalized.")
        if profile.risk_tolerance == "LOW":
            wait_score += 10
            wait_pos.append("Aligns with a low-risk profile seeking capital preservation.")
        
        wait_score = min(100, max(0, wait_score))
        results.append(self._build_result("WAIT_AND_ACCUMULATE_CAPITAL", wait_score, wait_pos, wait_neg, wait_risks, wait_limits))

        # Strategy 2: HOME_PURCHASE
        home_score = 50
        home_pos = []
        home_neg = []
        home_risks = []
        home_limits = []

        if profile.primary_goal == "BUY_HOME_TO_LIVE":
            home_score += weights["goal_alignment_bonus"]
            home_pos.append("Directly aligns with your primary goal of buying a home to live in.")
            if profile.home_ownership == "DOES_NOT_OWN_HOME":
                home_score += weights["no_home_bonus_for_home_purchase"]
                home_pos.append("Highly beneficial as you do not currently own residential property.")

        # Penalties/Gates
        if capacity["capacity_class"] == "CONSTRAINED":
            home_score = 10
            home_neg.append("Blocked/penalized due to constrained capital size.")
        elif capacity["capacity_class"] == "LIMITED":
            home_score = max(15, home_score - 25)
            home_neg.append("Limited capital reduces purchasing power for home acquisition.")

        if capacity["debt_burden_ratio"] > self.config["capacity"]["debt_burden_high"]:
            home_score -= weights["high_debt_penalty_on_home_purchase"]
            home_neg.append("High monthly debt service obligations restrict home mortgage capacity.")
            home_risks.append("Risk of payment defaults or high leverage burden.")

        if profile.horizon == "LESS_THAN_3_YEARS":
            home_score -= weights["short_horizon_penalty_on_home"]
            home_neg.append("Short investment horizon (<3 years) is incompatible with high transaction friction of home purchases.")
            home_risks.append("Illiquidity risk in case of sudden exit requirement.")

        home_score = min(100, max(0, home_score))
        results.append(self._build_result("HOME_PURCHASE", home_score, home_pos, home_neg, home_risks, home_limits))

        # Strategy 3: RENTAL_FLAT
        rental_score = 50
        rental_pos = []
        rental_neg = []
        rental_risks = []
        rental_limits = []

        if profile.primary_goal == "RENTAL_INCOME":
            rental_score += weights["goal_alignment_bonus"]
            rental_pos.append("Aligns with a cash-flow focused goal seeking periodic rental income.")
            
        if capacity["capacity_class"] in {"CONSTRAINED", "LIMITED"}:
            rental_score = min(20, rental_score - 30)
            rental_neg.append("Acquisition of a yield-generating flat typically requires substantial capital.")
        elif capacity["capacity_class"] in {"STRONG", "VERY_STRONG"}:
            rental_score += 15
            rental_pos.append("Strong capital capacity supports purchasing yield-generating apartments.")

        if profile.horizon == "LESS_THAN_3_YEARS":
            rental_score = min(15, rental_score - 40)
            rental_neg.append("Rental flat investments require a mid-to-long term horizon to recoup transaction costs.")

        if profile.liquidity_requirement == "HIGH":
            rental_score -= 20
            rental_neg.append("Residential real estate is highly illiquid; not suitable for high liquidity needs.")
            rental_risks.append("Difficulty executing a quick sale without significant price discounting.")

        rental_score = min(100, max(0, rental_score))
        results.append(self._build_result("RENTAL_FLAT", rental_score, rental_pos, rental_neg, rental_risks, rental_limits))

        # Strategy 4: LAND_APPRECIATION
        land_score = 45
        land_pos = []
        land_neg = []
        land_risks = []
        land_limits = []

        if profile.primary_goal == "LONG_TERM_APPRECIATION":
            land_score += weights["goal_alignment_bonus"]
            land_pos.append("Directly aligns with a wealth creation goal targeting long-term capital gains.")

        if profile.horizon in {"5_TO_10_YEARS", "MORE_THAN_10_YEARS"}:
            land_score += 15
            land_pos.append("Long-term horizon matches the typical holding period required for land appreciation.")
        
        # Hard Penalties/Gates
        if profile.liquidity_requirement == "HIGH":
            land_score -= weights["liquidity_penalty_on_land"]
            land_neg.append("High liquidity requirement strongly conflicts with raw land investments.")
            land_risks.append("Land plots are highly illiquid and may take months or years to dispose of at market value.")

        if profile.horizon == "LESS_THAN_3_YEARS":
            land_score -= weights["short_horizon_penalty_on_land"]
            land_neg.append("Short investment horizon (<3 years) makes infrastructure-dependent land investment extremely risky.")
            land_risks.append("Speculative loss risk due to delayed infrastructure execution.")

        if capacity["capacity_class"] in {"CONSTRAINED", "LIMITED"}:
            land_score = min(15, land_score - 25)
            land_neg.append("Constrained capital limits the ability to buy land in high-growth NCR corridors.")

        land_score = min(100, max(0, land_score))
        results.append(self._build_result("LAND_APPRECIATION", land_score, land_pos, land_neg, land_risks, land_limits))

        # Strategy 5: SHORT_TERM_RESALE
        resale_score = 30
        resale_pos = []
        resale_neg = []
        resale_risks = []
        resale_limits = ["NiveshMap lacks short-term transaction liquidity or resale velocity evidence; resale metrics cannot be strongly evaluated."]

        if profile.primary_goal == "BUY_AND_RESELL":
            resale_score += weights["goal_alignment_bonus"]
            resale_pos.append("Aligns with a short-term trading/resale investment objective.")

        if profile.risk_tolerance == "LOW":
            resale_score -= 50
            resale_neg.append("Low risk tolerance is incompatible with short-term resale strategies due to market volatility.")
            resale_risks.append("Market correction risk or liquidity lockup.")
        elif profile.risk_tolerance == "MODERATE":
            resale_score -= 25
            resale_neg.append("Short-term resale typically demands high risk tolerance.")

        if profile.horizon == "MORE_THAN_10_YEARS":
            resale_score -= 30
            resale_neg.append("A very long horizon is counter to a short-term resale/flip strategy.")

        # Cap score because of lack of transaction liquidity data
        resale_score = min(40, max(0, resale_score))
        results.append(self._build_result("SHORT_TERM_RESALE", resale_score, resale_pos, resale_neg, resale_risks, resale_limits))

        # Sort results: highest suitability first
        return sorted(results, key=lambda x: x["suitability_score"], reverse=True)

    def _build_result(self, strategy: str, score: float, pos: List[str], neg: List[str], risks: List[str], limits: List[str]) -> Dict[str, Any]:
        if score >= 75:
            band = "VERY_HIGH"
        elif score >= 50:
            band = "HIGH"
        elif score >= 25:
            band = "MODERATE"
        else:
            band = "LOW"

        return {
            "strategy": strategy,
            "suitability_score": int(score),
            "suitability_band": band,
            "positive_factors": pos,
            "negative_factors": neg,
            "major_risks": risks,
            "data_limitations": limits
        }


class LocationStrategyMatcher:
    """Matches scored strategies with specific locality and spatial metrics."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or load_suitability_config()

    def match_locality(self, strategy: str, locality_meta: Dict[str, Any], readiness_row: Optional[Dict[str, Any]], latest_row: Optional[Dict[str, Any]], scenario_upside: Optional[float] = None) -> Dict[str, Any]:
        """Match a strategy with locality analytical features.
        
        Args:
            strategy: Stated real-estate strategy.
            locality_meta: Locality dictionary metadata.
            readiness_row: Dictionary of data feasibility and readiness metrics.
            latest_row: Latest historical row dict containing distance & proxy rates.
            scenario_upside: Difference between Scenario A and Scenario C projected prices (numeric).
        """
        loc_id = locality_meta["locality_id"]
        loc_name = locality_meta["locality_name"]
        region = locality_meta["region"]

        # 1. Check for insufficient data
        if not readiness_row or not latest_row:
            return self._build_empty_match(loc_id, loc_name, region, strategy, "INSUFFICIENT_DATA", ["Locality lacks baseline quarterly observations or metrics."])

        readiness_class = readiness_row.get("readiness_class", "UNSUPPORTED")
        data_readiness_score = float(readiness_row.get("data_readiness_score", 0.0))

        if readiness_class == "UNSUPPORTED" or data_readiness_score < 30.0:
            return self._build_empty_match(loc_id, loc_name, region, strategy, "INSUFFICIENT_DATA", ["Data readiness score is below baseline threshold (30%).", f"Readiness class is {readiness_class}."])

        # 2. Score mapping
        match_score = 50
        supporting = []
        risks = []
        scenario_dependency = "LOW"

        if strategy == "WAIT_AND_ACCUMULATE_CAPITAL":
            return {
                "locality_id": loc_id,
                "locality": loc_name,
                "region": region,
                "strategy": strategy,
                "match_score": 0,
                "match_band": "N/A",
                "supporting_factors": ["Location search is not applicable for capital accumulation strategy."],
                "risk_factors": [],
                "data_readiness": f"{data_readiness_score:.0f}/100",
                "scenario_dependency": "LOW"
            }

        elif strategy == "LAND_APPRECIATION":
            # Prioritize proposed metro proximity, Jewar airport, and scenario upside
            proposed_metro = latest_row.get("distance_nearest_proposed_metro_km")
            airport_dist = latest_row.get("distance_airport_km")
            
            # Scenario exposure
            if scenario_upside and scenario_upside > 500:
                match_score += 15
                supporting.append(f"High sensitivity to infrastructure progression (Scenario A/C variance of ₹ {scenario_upside:.0f}/sqft).")
                scenario_dependency = "HIGH"
            elif scenario_upside and scenario_upside > 100:
                match_score += 5
                supporting.append(f"Moderate sensitivity to transit progression (Scenario variance: ₹ {scenario_upside:.0f}/sqft).")
                scenario_dependency = "MODERATE"
            else:
                risks.append("Weak scenario price upside under infrastructure progression.")

            # Proximity
            if proposed_metro is not None and proposed_metro <= 4.0:
                match_score += 15
                supporting.append(f"Proximity to proposed metro line corridor ({proposed_metro:.2f} km).")
            if airport_dist is not None and airport_dist <= 25.0:
                match_score += 10
                supporting.append(f"Located within the airport influence corridor ({airport_dist:.2f} km).")

            # Data readiness
            match_score += int((data_readiness_score - 50) / 2) # add/sub based on readiness

            # Penalize high infrastructure dependency if readiness is low or evidence is weak
            if data_readiness_score < 60.0:
                match_score -= 20
                risks.append("High infrastructure dependency with limited historical data depth.")

            # Penalize if nearest operational metro is extremely far (> 10km)
            op_metro = latest_row.get("distance_nearest_operational_metro_km")
            if op_metro is not None and op_metro > 10.0:
                risks.append(f"Currently isolated from operational transit hubs (operational metro is {op_metro:.2f} km away).")

        elif strategy == "RENTAL_FLAT":
            # Prioritize established connectivity and mature urban status
            op_metro = latest_row.get("distance_nearest_operational_metro_km")
            maturity = locality_meta.get("urban_maturity_class", "EMERGING")

            if op_metro is not None and op_metro <= 2.0:
                match_score += 20
                supporting.append(f"Excellent operational transit connectivity (metro station within {op_metro:.2f} km).")
            elif op_metro is not None and op_metro > 5.0:
                match_score -= 15
                risks.append(f"Poor operational metro connectivity ({op_metro:.2f} km distance) degrades rental attractiveness.")

            if maturity == "MATURE":
                match_score += 15
                supporting.append("Located in an established, high-demand mature residential sector.")
            elif maturity == "EMERGING":
                match_score -= 10
                risks.append("Emerging sector status; occupancy and rental yields may experience volatility.")

            match_score += int((data_readiness_score - 50) / 2)

        elif strategy == "HOME_PURCHASE":
            # Prioritize data readiness, established transit, low event risk
            op_metro = latest_row.get("distance_nearest_operational_metro_km")
            maturity = locality_meta.get("urban_maturity_class", "EMERGING")

            if op_metro is not None and op_metro <= 3.0:
                match_score += 15
                supporting.append(f"Comfortable proximity to operational metro station ({op_metro:.2f} km).")
            
            if maturity in {"MATURE", "TRANSITIONAL"}:
                match_score += 10
                supporting.append(f"Urban development class is {maturity}, indicating stable living amenities.")
            else:
                risks.append("Located in an emerging zone with ongoing construction and potential service delays.")

            match_score += int((data_readiness_score - 50) / 2)

        elif strategy == "SHORT_TERM_RESALE":
            # Be extremely conservative; short term resale lacks transaction liquidity
            match_score = 20
            risks.append("Short-term resale cannot be strongly evaluated due to a lack of transaction liquidity data.")

        # Clip scores
        match_score = min(100, max(0, match_score))
        if match_score >= 75:
            band = "HIGH"  # Let's map score to band
        elif match_score >= 45:
            band = "MODERATE"
        else:
            band = "LOW"

        return {
            "locality_id": loc_id,
            "locality": loc_name,
            "region": region,
            "strategy": strategy,
            "match_score": int(match_score),
            "match_band": band,
            "supporting_factors": supporting,
            "risk_factors": risks,
            "data_readiness": f"{data_readiness_score:.0f}/100",
            "scenario_dependency": scenario_dependency
        }

    def _build_empty_match(self, loc_id: str, loc_name: str, region: str, strategy: str, band: str, factors: List[str]) -> Dict[str, Any]:
        return {
            "locality_id": loc_id,
            "locality": loc_name,
            "region": region,
            "strategy": strategy,
            "match_score": 0,
            "match_band": band,
            "supporting_factors": [],
            "risk_factors": factors,
            "data_readiness": "N/A",
            "scenario_dependency": "LOW"
        }
