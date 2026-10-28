from sqlalchemy import text

from app.db.session import engine


def main() -> None:
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar_one()

            print(f"Database connection successful: {value}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()