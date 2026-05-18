"""CLI: python scripts/import_csv.py --file path/to/file.csv [--dry-run]"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, SessionLocal, engine
from app import models  # noqa: F401
from app.services.csv_import import parse_csv, import_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows = parse_csv(args.file)
    print(f"Parsed {len(rows)} rows")
    if args.dry_run:
        if rows:
            print("First row:", rows[0])
        return

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        result = import_rows(db, rows)
        print("Import result:", result)
    finally:
        db.close()


if __name__ == "__main__":
    main()
