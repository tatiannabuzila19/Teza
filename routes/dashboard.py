from fastapi import APIRouter, Depends
from typing import Optional
from services.auth_service import require_role
from services.dashboard_service import DashboardService

router = APIRouter()

@router.get("/dashboard-data")
async def dashboard_data(
    sex: Optional[str] = None,
    age_group: Optional[str] = None,
    domeniu: Optional[str] = None,
    current_user: dict = Depends(require_role("user", "admin", "analyst")),
):
    """
    Get aggregated dashboard data (8 charts).
    Accessible to all authenticated users.
    """
    return DashboardService.generate_dashboard_data(sex, age_group, domeniu)
