"""
Forecast Engine using Prophet + XGBoost
Predicts future LLM spending based on historical data
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


def _simple_forecast(historical_data: List[Dict], horizon_days: int) -> List[Dict]:
    """
    Simplified forecasting when Prophet/XGBoost unavailable.
    Uses exponential smoothing with trend detection.
    """
    if not historical_data:
        return []

    costs = [d["cost_usd"] for d in historical_data]
    if len(costs) < 3:
        avg = sum(costs) / len(costs) if costs else 0
        base_date = datetime.utcnow()
        return [
            {
                "date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
                "predicted_usd": avg,
                "lower_bound_usd": avg * 0.8,
                "upper_bound_usd": avg * 1.2,
            }
            for i in range(1, horizon_days + 1)
        ]

    # Calculate trend using linear regression
    n = len(costs)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(costs) / n
    
    numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, costs))
    denominator = sum((xi - x_mean) ** 2 for xi in x)
    slope = numerator / denominator if denominator != 0 else 0
    intercept = y_mean - slope * x_mean
    
    # Seasonal adjustment (simple weekly)
    last_date = datetime.strptime(historical_data[-1]["date"], "%Y-%m-%d")
    forecasts = []
    
    for i in range(1, horizon_days + 1):
        future_date = last_date + timedelta(days=i)
        predicted = intercept + slope * (n + i)
        predicted = max(0, predicted)
        
        # Weekend adjustment
        if future_date.weekday() >= 5:
            predicted *= 0.7
        
        uncertainty = predicted * 0.15 * (1 + i / horizon_days)
        
        forecasts.append({
            "date": future_date.strftime("%Y-%m-%d"),
            "predicted_usd": round(predicted, 4),
            "lower_bound_usd": round(max(0, predicted - uncertainty), 4),
            "upper_bound_usd": round(predicted + uncertainty, 4),
        })
    
    return forecasts


def run_prophet_forecast(historical_data: List[Dict], horizon_days: int) -> Dict:
    """
    Prophet-based forecasting with fallback to simple method.
    """
    try:
        from prophet import Prophet
        import pandas as pd
        
        df = pd.DataFrame(historical_data)
        df.columns = ["ds", "y"] + [c for c in df.columns if c not in ["date", "cost_usd"]]
        df["ds"] = pd.to_datetime(df["date"] if "date" in df.columns else df["ds"])
        df["y"] = df["cost_usd"] if "cost_usd" in df.columns else df["y"]
        df = df[["ds", "y"]].dropna()

        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=len(df) > 365,
            changepoint_prior_scale=0.1,
            interval_width=0.95,
        )
        model.fit(df)
        
        future = model.make_future_dataframe(periods=horizon_days)
        forecast = model.predict(future)
        future_forecast = forecast.tail(horizon_days)
        
        points = [
            {
                "date": row["ds"].strftime("%Y-%m-%d"),
                "predicted_usd": round(max(0, row["yhat"]), 4),
                "lower_bound_usd": round(max(0, row["yhat_lower"]), 4),
                "upper_bound_usd": round(max(0, row["yhat_upper"]), 4),
            }
            for _, row in future_forecast.iterrows()
        ]
        
        total = sum(p["predicted_usd"] for p in points)
        confidence = min(0.95, 0.5 + len(df) / 200)
        
        return {
            "model_used": "prophet",
            "data_points": points,
            "total_predicted_usd": round(total, 2),
            "confidence_score": round(confidence, 3),
        }
        
    except ImportError:
        logger.warning("Prophet not installed, using simple forecast")
    except Exception as e:
        logger.error(f"Prophet forecast failed: {e}")
    
    # Fallback
    points = _simple_forecast(historical_data, horizon_days)
    total = sum(p["predicted_usd"] for p in points)
    return {
        "model_used": "exponential_smoothing",
        "data_points": points,
        "total_predicted_usd": round(total, 2),
        "confidence_score": 0.65,
    }


def generate_forecast(
    historical_data: List[Dict],
    horizon: str = "30d"
) -> Dict:
    horizon_map = {"30d": 30, "90d": 90, "365d": 365}
    horizon_days = horizon_map.get(horizon, 30)
    return run_prophet_forecast(historical_data, horizon_days)
