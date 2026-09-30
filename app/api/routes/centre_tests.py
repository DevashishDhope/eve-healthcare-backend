import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.centre_test import CentreTest
from app.models.diagnostic_centre import DiagnosticCentre
from app.models.diagnostic_test import DiagnosticTest
from app.schemas.catalogue import CentreTestCreate, CentreTestResponse

router = APIRouter(prefix="/centre-tests", tags=["Centre Test Offerings"])


@router.post("", response_model=CentreTestResponse, status_code=status.HTTP_201_CREATED)
def create_centre_test(payload: CentreTestCreate, db: Session = Depends(get_db)):
    """Create a diagnostic test offering at a specific centre with pricing."""
    centre = db.query(DiagnosticCentre).filter(DiagnosticCentre.id == payload.centre_id).first()
    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic centre not found"
        )

    test = db.query(DiagnosticTest).filter(DiagnosticTest.id == payload.test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic test not found"
        )

    existing = db.query(CentreTest).filter(
        CentreTest.centre_id == payload.centre_id,
        CentreTest.test_id == payload.test_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This test is already offered at this diagnostic centre"
        )

    centre_test = CentreTest(
        centre_id=payload.centre_id,
        test_id=payload.test_id,
        price=payload.price
    )
    db.add(centre_test)
    try:
        db.commit()
        db.refresh(centre_test)
        return centre_test
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity conflict creating centre-test offering"
        )


@router.get("", response_model=List[CentreTestResponse])
def list_centre_tests(
    centre_id: Optional[uuid.UUID] = Query(None),
    test_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """List diagnostic test offerings, optionally filtered by centre or test."""
    query = db.query(CentreTest).options(joinedload(CentreTest.centre), joinedload(CentreTest.test))
    if centre_id:
        query = query.filter(CentreTest.centre_id == centre_id)
    if test_id:
        query = query.filter(CentreTest.test_id == test_id)
    return query.all()


@router.get("/{centre_test_id}", response_model=CentreTestResponse)
def get_centre_test(centre_test_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve details of a specific centre-test offering with price."""
    centre_test = (
        db.query(CentreTest)
        .options(joinedload(CentreTest.centre), joinedload(CentreTest.test))
        .filter(CentreTest.id == centre_test_id)
        .first()
    )
    if not centre_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Centre-test offering not found"
        )
    return centre_test
