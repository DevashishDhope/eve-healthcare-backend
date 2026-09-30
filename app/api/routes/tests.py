import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.diagnostic_test import DiagnosticTest
from app.schemas.catalogue import DiagnosticTestCreate, DiagnosticTestResponse

router = APIRouter(prefix="/tests", tags=["Diagnostic Tests"])


@router.post("", response_model=DiagnosticTestResponse, status_code=status.HTTP_201_CREATED)
def create_test(payload: DiagnosticTestCreate, db: Session = Depends(get_db)):
    """Create a new diagnostic test."""
    test = DiagnosticTest(
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None
    )
    db.add(test)
    db.commit()
    db.refresh(test)
    return test


@router.get("", response_model=List[DiagnosticTestResponse])
def list_tests(db: Session = Depends(get_db)):
    """List all available diagnostic tests."""
    return db.query(DiagnosticTest).order_by(DiagnosticTest.name).all()


@router.get("/{test_id}", response_model=DiagnosticTestResponse)
def get_test(test_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve details of a specific diagnostic test."""
    test = db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic test not found"
        )
    return test
