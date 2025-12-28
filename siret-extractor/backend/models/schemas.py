"""Pydantic models for the SIRET extractor."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum
import re


class JobStatus(str, Enum):
    """Status of an extraction job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractionRequest(BaseModel):
    """Request body for extraction endpoint."""
    sirets: list[str] = Field(..., min_length=1, description="List of SIRET numbers")

    @field_validator("sirets")
    @classmethod
    def validate_sirets(cls, v: list[str]) -> list[str]:
        """Validate and clean SIRET numbers."""
        cleaned = []
        for siret in v:
            # Remove spaces and special characters
            clean = re.sub(r"[^0-9]", "", siret)
            if clean:
                cleaned.append(clean)
        return cleaned


class Dirigeant(BaseModel):
    """Information about a company director."""
    civilite: str = ""
    nom: str = ""
    prenom: str = ""
    fonction: str = ""


class CompanyData(BaseModel):
    """Extracted company data."""
    siret: str
    raison_sociale: str = ""
    rcs: str = ""
    forme_juridique: str = ""
    capital: str = ""
    tva_intracommunautaire: str = ""
    code_ape: str = ""
    adresse: str = ""
    code_postal: str = ""
    ville: str = ""
    pays: str = "France"
    civilite_contact: str = ""
    nom_contact: str = ""
    prenom_contact: str = ""
    fonction_contact: str = ""
    erreur: Optional[str] = None
    donnees_partielles: bool = False


class JobResponse(BaseModel):
    """Response after creating an extraction job."""
    job_id: str
    message: str = "Job created successfully"


class JobStatusResponse(BaseModel):
    """Response for job status endpoint."""
    job_id: str
    status: JobStatus
    progress: int = 0
    total: int = 0
    message: Optional[str] = None


class JobResultsResponse(BaseModel):
    """Response for job results endpoint."""
    job_id: str
    status: JobStatus
    data: list[CompanyData] = []
    errors: list[dict] = []
    total_processed: int = 0
    total_success: int = 0
    total_errors: int = 0


class ErrorDetail(BaseModel):
    """Details about an extraction error."""
    siret: str
    error_type: str
    message: str
    source: str = ""  # "INSEE", "RNE", or "VALIDATION"
