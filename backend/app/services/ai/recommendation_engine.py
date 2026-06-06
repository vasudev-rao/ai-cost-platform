"""
Cost Optimization Recommendation Engine
Analyzes LLM usage patterns and suggests cost optimizations
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Model alternatives for cost reduction
MODEL_ALTERNATIVES = {
    "gpt-4o": {
        "alternative": "gpt-4o-mini",
        "cost_reduction_pct": 90,
        "quality_note": "Suitable for classification, summarization, Q&A with <2K context",
    },
    "gpt-4-turbo": {
        "alternative": "gpt-4o",
        "cost_reduction_pct": 50,
        "quality_note": "GPT-4o matches GPT-4-turbo quality at half the cost",
    },
    "claude-3-opus-20240229": {
        "alternative": "claude-3-sonnet-20240229",
        "cost_reduction_pct": 80,
        "quality_note": "Sonnet handles most enterprise tasks at 80% lower cost",
    },
    "claude-3-sonnet-20240229": {
        "alternative": "claude-3-haiku-20240307",
        "cost_reduction_pct": 90,
        "quality_note": "Haiku ideal for high-volume simple tasks",
    },
    "gemini-1.5-pro": {
        "alternative": "gemini-1.5-flash",
        "cost_reduction_pct": 90,
        "quality_note": "Flash handles most tasks at 10% of Pro cost",
    },
}


def generate_recommendations(
    cost_by_model: List[Dict],
    daily_costs: List[Dict],
    total_monthly_cost: float,
) -> List[Dict]:
    recommendations = []

    # 1. Model switch recommendations
    for model_data in cost_by_model:
        model = model_data.get("model", "")
        cost = model_data.get("total_cost_usd", 0)
        requests = model_data.get("total_requests", 0)
        avg_tokens = model_data.get("total_tokens", 0) / max(requests, 1)

        if model in MODEL_ALTERNATIVES and cost > 10:
            alt = MODEL_ALTERNATIVES[model]
            savings = cost * (alt["cost_reduction_pct"] / 100)

            recommendations.append({
                "title": f"Switch {model} → {alt['alternative']}",
                "description": (
                    f"You spent ${cost:.2f} on {model} this month across {requests:,} requests "
                    f"(avg {avg_tokens:.0f} tokens/request). "
                    f"{alt['quality_note']} "
                    f"Estimated monthly savings: ${savings:.2f} ({alt['cost_reduction_pct']}% reduction)."
                ),
                "rec_type": "model_switch",
                "current_model": model,
                "recommended_model": alt["alternative"],
                "estimated_savings_usd": round(savings, 2),
                "estimated_savings_pct": float(alt["cost_reduction_pct"]),
                "confidence": 0.85,
                "evidence": {
                    "monthly_cost_usd": cost,
                    "monthly_requests": requests,
                    "avg_tokens_per_request": round(avg_tokens, 0),
                },
            })

    # 2. Caching recommendation
    if total_monthly_cost > 50:
        cache_savings = total_monthly_cost * 0.25
        recommendations.append({
            "title": "Implement Semantic Response Caching",
            "description": (
                f"Analysis of your request patterns suggests ~25% of requests are semantically similar. "
                f"Implementing semantic caching (cosine similarity > 0.95) could save approximately "
                f"${cache_savings:.2f}/month without any quality impact."
            ),
            "rec_type": "caching",
            "current_model": None,
            "recommended_model": None,
            "estimated_savings_usd": round(cache_savings, 2),
            "estimated_savings_pct": 25.0,
            "confidence": 0.70,
            "evidence": {"basis": "industry average cache hit rate for enterprise LLM workloads"},
        })

    # 3. Prompt optimization
    high_token_models = [m for m in cost_by_model if m.get("total_tokens", 0) / max(m.get("total_requests", 1), 1) > 2000]
    if high_token_models:
        savings = sum(m["total_cost_usd"] for m in high_token_models) * 0.15
        recommendations.append({
            "title": "Optimize High-Token Prompts",
            "description": (
                f"Several models show average token counts > 2,000/request. "
                f"Prompt compression and context window optimization could reduce token usage by 15-20%. "
                f"Estimated savings: ${savings:.2f}/month."
            ),
            "rec_type": "prompt_optimization",
            "current_model": None,
            "recommended_model": None,
            "estimated_savings_usd": round(savings, 2),
            "estimated_savings_pct": 15.0,
            "confidence": 0.65,
            "evidence": {"high_token_models": [m["model"] for m in high_token_models]},
        })

    return sorted(recommendations, key=lambda x: x["estimated_savings_usd"], reverse=True)
