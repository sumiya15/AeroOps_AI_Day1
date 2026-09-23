from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ScenarioSummary
from app.seed import seed_demo_data
from app.services.scenario import get_demo_summary


router = APIRouter(prefix="/api/v1/demo", tags=["demo"])


@router.get("/summary", response_model=ScenarioSummary)
def summary(db: Session = Depends(get_db)) -> ScenarioSummary:
    try:
        return get_demo_summary(db)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.post("/reset", response_model=ScenarioSummary)
def reset(db: Session = Depends(get_db)) -> ScenarioSummary:
    seed_demo_data(db)
    return get_demo_summary(db)

