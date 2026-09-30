import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.diagnostic_centre import DiagnosticCentre
from app.schemas.catalogue import DiagnosticCentreCreate, DiagnosticCentreResponse

router = APIRouter(prefix="/centres", tags=["Diagnostic Centres"])


@router.post("", response_model=DiagnosticCentreResponse, status_code=status.HTTP_201_CREATED)
def create_centre(payload: DiagnosticCentreCreate, db: Session = Depends(get_db)):
    """Create a new diagnostic centre."""
    centre = DiagnosticCentre(
        name=payload.name.strip(),
        location=payload.location.strip()
    )
    db.add(centre)
    db.commit()
    db.refresh(centre)
    return centre


@router.get("", response_model=List[DiagnosticCentreResponse])
def list_centres(db: Session = Depends(get_db)):
    """List all available diagnostic centres."""
    return db.query(DiagnosticCentre).order_by(DiagnosticCentre.name).all()


@router.get("/{centre_id}", response_model=DiagnosticCentreResponse)
def get_centre(centre_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve details of a specific diagnostic centre."""
    centre = db.query(DiagnosticCentre).filter(DiagnosticCentre.id == centre_id).first()
    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic centre not found"
        )
    return centre
