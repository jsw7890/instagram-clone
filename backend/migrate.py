#!/usr/bin/env python3
"""Apply SQLite schema: create missing tables + incremental upgrades."""

from app.database import Base, engine, run_migrations
from app.models import *  # noqa: F401,F403


def main() -> None:
    Base.metadata.create_all(bind=engine)
    run_migrations()
    print("Migration complete (schema version recorded).")


if __name__ == "__main__":
    main()
