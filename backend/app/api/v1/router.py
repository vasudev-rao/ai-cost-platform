from fastapi import APIRouter
from app.api.v1.endpoints import auth, costs, forecasts, recommendations, alerts, organizations, teams, projects, reports

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(teams.router, prefix="/teams", tags=["Teams"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(costs.router, prefix="/costs", tags=["Costs"])
api_router.include_router(forecasts.router, prefix="/forecasts", tags=["Forecasts"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
