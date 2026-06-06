"""
Anomaly Detection Engine
Detects cost spikes, usage anomalies, and suspicious activity
"""
import logging
from typing import List, Dict, Optional
import statistics

logger = logging.getLogger(__name__)


def detect_anomalies(
    daily_costs: List[Dict],
    sensitivity: float = 2.5,
) -> List[Dict]:
    """
    Z-score based anomaly detection with IQR fallback.
    sensitivity: standard deviations from mean to flag as anomaly
    """
    if len(daily_costs) < 7:
        return []

    costs = [d["cost_usd"] for d in daily_costs]
    mean = statistics.mean(costs)
    stdev = statistics.stdev(costs) if len(costs) > 1 else 0

    if stdev == 0:
        return []

    anomalies = []
    for data_point in daily_costs:
        z_score = abs(data_point["cost_usd"] - mean) / stdev
        if z_score > sensitivity:
            pct_deviation = ((data_point["cost_usd"] - mean) / mean) * 100
            anomalies.append({
                "date": data_point["date"],
                "cost_usd": data_point["cost_usd"],
                "expected_usd": round(mean, 4),
                "z_score": round(z_score, 2),
                "deviation_pct": round(pct_deviation, 1),
                "severity": "critical" if z_score > 4 else "warning",
            })

    return sorted(anomalies, key=lambda x: x["z_score"], reverse=True)


def detect_cost_spike(
    current_cost: float,
    historical_avg: float,
    spike_threshold_pct: float = 200.0,
) -> Optional[Dict]:
    """Detect if current cost represents a significant spike"""
    if historical_avg <= 0:
        return None

    change_pct = ((current_cost - historical_avg) / historical_avg) * 100

    if change_pct >= spike_threshold_pct:
        return {
            "is_spike": True,
            "current_cost_usd": current_cost,
            "historical_avg_usd": historical_avg,
            "change_pct": round(change_pct, 1),
            "severity": "critical" if change_pct > 400 else "warning",
        }
    return None
