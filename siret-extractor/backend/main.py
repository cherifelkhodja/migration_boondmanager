"""FastAPI backend for SIRET extractor."""
import asyncio
import csv
import io
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd

from config import get_settings
from models.schemas import (
    ExtractionRequest,
    JobResponse,
    JobStatus,
    JobStatusResponse,
    JobResultsResponse,
    CompanyData,
)
from services.data_processor import DataProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SIRET Extractor API",
    description="API pour extraire les informations d'entreprises francaises a partir de numeros SIRET",
    version="1.0.0",
)

# Get settings
settings = get_settings()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage (in production, use Redis or database)
jobs: dict[str, dict] = {}


def generate_job_id() -> str:
    """Generate a unique job ID."""
    return str(uuid.uuid4())


async def process_job(job_id: str, sirets: list[str]) -> None:
    """Background task to process SIRET extraction.

    Args:
        job_id: Unique job identifier
        sirets: List of SIRET numbers to process
    """
    jobs[job_id]["status"] = JobStatus.PROCESSING
    jobs[job_id]["started_at"] = datetime.now().isoformat()

    processor = DataProcessor()
    results: list[CompanyData] = []
    errors: list[dict] = []

    total = len(sirets)
    jobs[job_id]["total"] = total

    for i, siret in enumerate(sirets):
        try:
            result = await processor.process_siret(siret)
            results.append(result)

            if result.erreur:
                errors.append({
                    "siret": siret,
                    "error": result.erreur,
                    "partial": result.donnees_partielles,
                })
        except Exception as e:
            logger.error(f"Error processing {siret}: {e}")
            results.append(CompanyData(siret=siret, erreur=str(e)))
            errors.append({
                "siret": siret,
                "error": str(e),
                "partial": False,
            })

        # Update progress
        jobs[job_id]["progress"] = i + 1

    # Mark job as completed
    jobs[job_id]["status"] = JobStatus.COMPLETED
    jobs[job_id]["completed_at"] = datetime.now().isoformat()
    jobs[job_id]["results"] = results
    jobs[job_id]["errors"] = errors


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "SIRET Extractor API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/extract", response_model=JobResponse)
async def create_extraction_job(
    request: ExtractionRequest,
    background_tasks: BackgroundTasks,
):
    """Create a new extraction job.

    Args:
        request: Request containing list of SIRET numbers
        background_tasks: FastAPI background tasks

    Returns:
        Job ID and status message
    """
    if not request.sirets:
        raise HTTPException(status_code=400, detail="No SIRET numbers provided")

    job_id = generate_job_id()

    # Initialize job
    jobs[job_id] = {
        "status": JobStatus.PENDING,
        "progress": 0,
        "total": len(request.sirets),
        "sirets": request.sirets,
        "results": [],
        "errors": [],
        "created_at": datetime.now().isoformat(),
    }

    # Start background processing
    background_tasks.add_task(process_job, job_id, request.sirets)

    return JobResponse(
        job_id=job_id,
        message=f"Job created with {len(request.sirets)} SIRET numbers",
    )


@app.post("/api/upload", response_model=JobResponse)
async def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Upload a CSV file with SIRET numbers.

    Args:
        file: CSV file with SIRET column
        background_tasks: FastAPI background tasks

    Returns:
        Job ID and status message
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    # Read file content
    content = await file.read()

    try:
        # Try to decode and parse CSV
        text = content.decode("utf-8-sig")  # Handle BOM
        reader = csv.DictReader(io.StringIO(text), delimiter=";")

        # Find SIRET column
        sirets = []
        siret_column = None

        # Check for SIRET column name
        if reader.fieldnames:
            for col in reader.fieldnames:
                if col.lower().strip() in ("siret", "siret_number", "numero_siret"):
                    siret_column = col
                    break

            # If no named column, check if there's only one column
            if not siret_column and len(reader.fieldnames) == 1:
                siret_column = reader.fieldnames[0]

        if not siret_column:
            # Try comma delimiter
            text = content.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text), delimiter=",")

            if reader.fieldnames:
                for col in reader.fieldnames:
                    if col.lower().strip() in ("siret", "siret_number", "numero_siret"):
                        siret_column = col
                        break

                if not siret_column and len(reader.fieldnames) == 1:
                    siret_column = reader.fieldnames[0]

        if not siret_column:
            raise HTTPException(
                status_code=400,
                detail="Could not find SIRET column in CSV",
            )

        # Re-read with correct delimiter
        text = content.decode("utf-8-sig")
        delimiter = ";" if ";" in text else ","
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

        for row in reader:
            siret = row.get(siret_column, "").strip()
            if siret:
                # Clean SIRET
                clean = "".join(c for c in siret if c.isdigit())
                if clean:
                    sirets.append(clean)

    except Exception as e:
        logger.error(f"Error parsing CSV: {e}")
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")

    if not sirets:
        raise HTTPException(status_code=400, detail="No valid SIRET numbers found in CSV")

    # Create job
    job_id = generate_job_id()
    jobs[job_id] = {
        "status": JobStatus.PENDING,
        "progress": 0,
        "total": len(sirets),
        "sirets": sirets,
        "results": [],
        "errors": [],
        "created_at": datetime.now().isoformat(),
    }

    # Start background processing
    background_tasks.add_task(process_job, job_id, sirets)

    return JobResponse(
        job_id=job_id,
        message=f"Job created with {len(sirets)} SIRET numbers from CSV",
    )


@app.get("/api/job/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status of an extraction job.

    Args:
        job_id: Job identifier

    Returns:
        Job status and progress
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        total=job["total"],
    )


@app.get("/api/job/{job_id}/results", response_model=JobResultsResponse)
async def get_job_results(job_id: str):
    """Get the results of an extraction job.

    Args:
        job_id: Job identifier

    Returns:
        Job results and statistics
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] not in (JobStatus.COMPLETED, JobStatus.PROCESSING):
        raise HTTPException(
            status_code=400,
            detail="Job has not started or is still pending",
        )

    results = job.get("results", [])
    errors = job.get("errors", [])

    # Count successes (no errors or partial data)
    total_success = sum(1 for r in results if not r.erreur or r.donnees_partielles)
    total_errors = sum(1 for r in results if r.erreur and not r.donnees_partielles)

    return JobResultsResponse(
        job_id=job_id,
        status=job["status"],
        data=results,
        errors=errors,
        total_processed=len(results),
        total_success=total_success,
        total_errors=total_errors,
    )


@app.get("/api/job/{job_id}/download")
async def download_results(job_id: str, format: str = "csv"):
    """Download extraction results as CSV or Excel.

    Args:
        job_id: Job identifier
        format: Output format (csv or xlsx)

    Returns:
        File download response
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed yet")

    results = job.get("results", [])

    if not results:
        raise HTTPException(status_code=400, detail="No results to download")

    # Convert to DataFrame
    data = []
    for r in results:
        data.append({
            "Siret": r.siret,
            "Raison sociale": r.raison_sociale,
            "RCS": r.rcs,
            "Forme": r.forme_juridique,
            "Capital": r.capital,
            "TVA": r.tva_intracommunautaire,
            "APE": r.code_ape,
            "Adresse": r.adresse,
            "Code postal": r.code_postal,
            "Ville": r.ville,
            "Pays": r.pays,
            "Civilite contact": r.civilite_contact,
            "Nom contact": r.nom_contact,
            "Prenom contact": r.prenom_contact,
            "Fonction contact": r.fonction_contact,
        })

    df = pd.DataFrame(data)

    if format.lower() == "xlsx":
        # Excel format
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Resultats")
        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=extraction_{job_id}.xlsx"
            },
        )
    else:
        # CSV format
        output = io.StringIO()
        df.to_csv(output, index=False, sep=";", encoding="utf-8")
        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=extraction_{job_id}.csv"
            },
        )


@app.delete("/api/job/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its results.

    Args:
        job_id: Job identifier

    Returns:
        Confirmation message
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    del jobs[job_id]
    return {"message": "Job deleted successfully"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )
