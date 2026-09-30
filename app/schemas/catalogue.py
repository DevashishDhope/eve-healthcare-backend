import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class DiagnosticCentreCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    location: str = Field(..., min_length=1, max_length=300)


class DiagnosticCentreResponse(BaseModel):
    id: uuid.UUID
    name: str
    location: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DiagnosticTestCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class DiagnosticTestResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CentreTestCreate(BaseModel):
    centre_id: uuid.UUID
    test_id: uuid.UUID
    price: Decimal = Field(..., ge=0, description="Test price at this centre")


class CentreTestResponse(BaseModel):
    id: uuid.UUID
    centre_id: uuid.UUID
    test_id: uuid.UUID
    price: Decimal
    created_at: datetime
    centre: Optional[DiagnosticCentreResponse] = None
    test: Optional[DiagnosticTestResponse] = None

    model_config = ConfigDict(from_attributes=True)
