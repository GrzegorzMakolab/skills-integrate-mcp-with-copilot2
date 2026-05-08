from pathlib import Path

from db import Database


BASE_DIR = Path(__file__).parent
DB = Database(
    db_path=BASE_DIR / "school.db",
    schema_path=BASE_DIR / "db" / "schema.sql",
    seed_path=BASE_DIR / "db" / "seed.sql",
)


def main() -> None:
    DB.initialize(with_seed=True)
    print(f"Database initialized at {DB.db_path}")


if __name__ == "__main__":
    main()
