import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, engine
from app import models  # noqa: F401 (register tables)


def init_db():
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at: {engine.url}")


if __name__ == "__main__":
    init_db()
