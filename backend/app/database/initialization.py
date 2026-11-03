"""Database initialization routine."""

import logging
from app.database.connection import Base, engine
import app.models  # noqa: F401 - ensure models are registered with Base metadata

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Creates database tables if they do not exist."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")


if __name__ == "__main__":
    init_db()
