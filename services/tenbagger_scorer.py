"""
Tenbagger scoring system - calculates 0-100 score based on multiple growth metrics.
"""

from typing import Dict, Any
import pandas as pd


class TenbaggerScorer:
    """
    Calculate Tenbagger potential score (0-100) based on 10 key metrics.
    Each metric contributes 0-10 points.
    """
    
    def __init__(self):
        # Default weights (can be customized)
        self.weights = {
            "revenue_growth": 1.0,
            "earnings_growth": 1.0,
            "peg_ratio": 1.0,
            "roe": 1.0,
            "profit_margin_quality": 1.0,
            "financial_health": 1.0,
            "momentum": 1.0,
            "relative_strength": 1.0,
            "institutional_ownership": 1.0,
            "market_cap_sweet_spot": 1.0
        }
    
    def score_revenue_growth(self, growth: float) -> float:
        """Score revenue growth (YoY %)."""
        if growth >= 50:
            return 10.0
        elif growth >= 30:
            return 7.0 + (growth - 30) / 20 * 3  # Linear between 7-10
        elif growth >= 20:
            return 5.0 + (growth - 20) / 10 * 2  # Linear between 5-7
        elif growth >= 10:
            return 2.0 + (growth - 10) / 10 * 3  # Linear between 2-5
        elif growth >= 0:
            return growth / 10 * 2  # Linear between 0-2
        else:
            return 0.0
    
    def score_earnings_growth(self, growth: float) -> float:
        """Score earnings growth (YoY %)."""
        if growth >= 50:
            return 10.0
        elif growth >= 30:
            return 7.0 + (growth - 30) / 20 * 3
        elif growth >= 20:
            return 5.0 + (growth - 20) / 10 * 2
        elif growth >= 10:
            return 2.0 + (growth - 10) / 10 * 3
        elif growth >= 0:
            return growth / 10 * 2
        else:
            return 0.0
    
    def score_peg_ratio(self, peg: float) -> float:
        """Score PEG ratio (lower is better, but must be positive)."""
        if peg <= 0:
            return 0.0  # Negative PEG is meaningless
        elif peg < 0.5:
            return 10.0
        elif peg <= 1.0:
            return 7.0 + (1.0 - peg) / 0.5 * 3  # Linear 7-10
        elif peg <= 1.5:
            return 3.0 + (1.5 - peg) / 0.5 * 4  # Linear 3-7
        elif peg <= 2.0:
            return (2.0 - peg) / 0.5 * 3  # Linear 0-3
        else:
            return 0.0
    
    def score_roe(self, roe: float) -> float:
        """Score Return on Equity (%)."""
        if roe >= 25:
            return 10.0
        elif roe >= 20:
            return 7.0 + (roe - 20) / 5 * 3
        elif roe >= 15:
            return 5.0 + (roe - 15) / 5 * 2
        elif roe >= 10:
            return 2.0 + (roe - 10) / 5 * 3
        elif roe >= 0:
            return roe / 10 * 2
        else:
            return 0.0
    
    def score_profit_margin(self, margin: float) -> float:
        """Score profit margin (%)."""
        if margin >= 25:
            return 10.0
        elif margin >= 20:
            return 7.0 + (margin - 20) / 5 * 3
        elif margin >= 15:
            return 5.0 + (margin - 15) / 5 * 2
        elif margin >= 10:
            return 3.0 + (margin - 10) / 5 * 2
        elif margin >= 5:
            return margin / 5 * 3
        else:
            return 0.0
    
    def score_financial_health(self, debt_to_equity: float, current_ratio: float) -> float:
        """Score financial health based on debt and liquidity."""
        debt_score = 0.0
        if debt_to_equity < 0.3:
            debt_score = 10.0
        elif debt_to_equity <= 0.7:
            debt_score = 7.0 + (0.7 - debt_to_equity) / 0.4 * 3
        elif debt_to_equity <= 1.5:
            debt_score = 3.0 + (1.5 - debt_to_equity) / 0.8 * 4
        else:
            debt_score = max(0, 3.0 - (debt_to_equity - 1.5) * 0.5)
        
        # Bonus for good current ratio
        liquidity_bonus = 0.0
        if current_ratio >= 2.0:
            liquidity_bonus = 0.0  # Already good
        elif current_ratio >= 1.5:
            liquidity_bonus = 0.0
        
        return min(10.0, debt_score + liquidity_bonus)
    
    def score_momentum(self, price_change_6m: float) -> float:
        """Score 6-month price momentum (%)."""
        if price_change_6m >= 50:
            return 10.0
        elif price_change_6m >= 30:
            return 7.0 + (price_change_6m - 30) / 20 * 3
        elif price_change_6m >= 15:
            return 4.0 + (price_change_6m - 15) / 15 * 3
        elif price_change_6m >= 0:
            return price_change_6m / 15 * 4
        elif price_change_6m >= -15:
            return 0.0  # Slight loss, no points
        else:
            return 0.0  # Negative momentum
    
    def score_relative_strength(self, distance_from_52w_high: float) -> float:
        """Score based on proximity to 52-week high (%)."""
        # distance_from_52w_high is negative if below high
        if distance_from_52w_high >= -5:  # Within 5% of high
            return 10.0
        elif distance_from_52w_high >= -10:
            return 7.0 + (distance_from_52w_high + 10) / 5 * 3
        elif distance_from_52w_high >= -20:
            return 3.0 + (distance_from_52w_high + 20) / 10 * 4
        elif distance_from_52w_high >= -30:
            return (distance_from_52w_high + 30) / 10 * 3
        else:
            return 0.0
    
    def score_institutional_ownership(self, ownership_pct: float) -> float:
        """Score institutional ownership (sweet spot 30-70%)."""
        if 30 <= ownership_pct <= 70:
            return 10.0
        elif 70 < ownership_pct <= 85:
            return 7.0 - (ownership_pct - 70) / 15 * 4
        elif 20 <= ownership_pct < 30:
            return 5.0 + (ownership_pct - 20) / 10 * 5
        elif 85 < ownership_pct <= 95:
            return max(0, 3.0 - (ownership_pct - 85) / 10 * 3)
        elif ownership_pct < 20:
            return ownership_pct / 20 * 5
        else:
            return 0.0
    
    def score_market_cap_sweet_spot(self, market_cap: float) -> float:
        """Score market cap (small-mid cap preferred for growth)."""
        # Convert to billions for easier reading
        cap_b = market_cap / 1e9
        
        if 0.5 <= cap_b <= 5:  # $500M - $5B sweet spot
            return 10.0
        elif 0.2 <= cap_b < 0.5:  # $200M - $500M
            return 7.0 + (cap_b - 0.2) / 0.3 * 3
        elif 5 < cap_b <= 10:  # $5B - $10B
            return 7.0 - (cap_b - 5) / 5 * 4
        elif 10 < cap_b <= 50:  # $10B - $50B
            return max(0, 3.0 - (cap_b - 10) / 40 * 3)
        elif cap_b < 0.2:  # Too small (risky)
            return cap_b / 0.2 * 5
        else:  # Too large (less growth potential)
            return 0.0
    
    def calculate_score(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive tenbagger score.
        
        Returns dict with:
            - total_score: 0-100
            - individual_scores: breakdown by metric
            - risk_level: Low/Medium/High
        """
        scores = {}
        
        # Calculate individual scores
        scores["revenue_growth"] = self.score_revenue_growth(stock_data.get("revenue_growth", 0))
        scores["earnings_growth"] = self.score_earnings_growth(stock_data.get("earnings_growth", 0))
        scores["peg_ratio"] = self.score_peg_ratio(stock_data.get("peg_ratio", 99))
        scores["roe"] = self.score_roe(stock_data.get("roe", 0))
        scores["profit_margin"] = self.score_profit_margin(stock_data.get("profit_margin", 0))
        scores["financial_health"] = self.score_financial_health(
            stock_data.get("debt_to_equity", 0),
            stock_data.get("current_ratio", 1)
        )
        scores["momentum"] = self.score_momentum(stock_data.get("price_change_6m", 0))
        scores["relative_strength"] = self.score_relative_strength(stock_data.get("distance_from_52w_high", -100))
        scores["institutional_ownership"] = self.score_institutional_ownership(stock_data.get("institutional_ownership", 0))
        scores["market_cap"] = self.score_market_cap_sweet_spot(stock_data.get("market_cap", 0))
        
        # Apply weights and calculate total
        weighted_scores = {k: v * self.weights.get(k, 1.0) for k, v in scores.items()}
        total_weight = sum(self.weights.values())
        total_score = sum(weighted_scores.values()) / total_weight * 10  # Normalize to 0-100
        
        # Determine risk level
        debt_ratio = stock_data.get("debt_to_equity", 0)
        volatility_proxy = abs(stock_data.get("price_change_6m", 0))
        
        if debt_ratio > 1.5 or volatility_proxy > 50:
            risk_level = "High"
        elif debt_ratio > 0.7 or volatility_proxy > 30:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        
        return {
            "total_score": round(total_score, 1),
            "individual_scores": {k: round(v, 1) for k, v in scores.items()},
            "risk_level": risk_level,
            "weighted_scores": {k: round(v, 1) for k, v in weighted_scores.items()}
        }


def score_stocks_dataframe(df: pd.DataFrame, custom_weights: Dict[str, float] = None) -> pd.DataFrame:
    """
    Add tenbagger scores to a DataFrame of stocks.
    
    Args:
        df: DataFrame with stock data
        custom_weights: Optional custom weights for scoring
        
    Returns:
        DataFrame with added score columns
    """
    if df.empty:
        return df
    
    scorer = TenbaggerScorer()
    if custom_weights:
        scorer.weights.update(custom_weights)
    
    scores_list = []
    for _, row in df.iterrows():
        score_data = scorer.calculate_score(row.to_dict())
        scores_list.append(score_data)
    
    df["tenbagger_score"] = [s["total_score"] for s in scores_list]
    df["risk_level"] = [s["risk_level"] for s in scores_list]
    
    # Add detailed scores as separate columns (optional)
    for metric in scores_list[0]["individual_scores"].keys():
        df[f"score_{metric}"] = [s["individual_scores"][metric] for s in scores_list]
    
    return df
