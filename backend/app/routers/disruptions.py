from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Disruption
from app.schemas import AffectedPassengerOut
from app.services.impact import get_affected_passengers


router = APIRouter(prefix="/api/v1/disruptions", tags=["disruptions"])


@router.get(
    "/{disruption_id}/affected-passengers",
    response_model=list[AffectedPassengerOut],
)
def affected_passengers(
    disruption_id: int, db: Session = Depends(get_db)
) -> list[AffectedPassengerOut]:
    disruption = db.get(Disruption, disruption_id)
    if disruption is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Disruption not found",
        )
    return get_affected_passengers(db, disruption)

