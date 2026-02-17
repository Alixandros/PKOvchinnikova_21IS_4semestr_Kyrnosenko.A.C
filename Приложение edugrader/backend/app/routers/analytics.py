from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, auth
from ..dependencies import get_db

router = APIRouter()

@router.get("/student/{student_id}")
async def get_student_analytics(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return {"message": "Аналитика в разработке"}