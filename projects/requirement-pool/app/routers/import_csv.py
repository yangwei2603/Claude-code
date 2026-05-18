import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.csv_import import parse_csv, import_rows

router = APIRouter()


@router.post("/import/csv")
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)
    try:
        rows = parse_csv(tmp_path)
        result = import_rows(db, rows)
    finally:
        tmp_path.unlink(missing_ok=True)
    return {"code": 0, "message": "success", "data": result}
