"""
Database connection and session management.
Follows dependency injection pattern - services receive database sessions.
"""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from src.config import settings
from src.database.models import Base
import logging

logger = logging.getLogger(__name__)


class Database:
    """Database manager following singleton pattern."""

    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize database connection."""
        if self._engine is None:
            self._initialize_engine()

    def _initialize_engine(self):
        """Create database engine with appropriate configuration."""
        connection_args = {}

        # SQLite specific configuration
        if settings.database_url.startswith("sqlite"):
            connection_args = {
                "check_same_thread": False,
                "poolclass": StaticPool,
            }
            logger.info(f"Initializing SQLite database: {settings.database_url}")
        else:
            # PostgreSQL configuration
            logger.info(f"Initializing PostgreSQL database")

        self._engine = create_engine(
            settings.database_url,
            connect_args=connection_args,
            echo=False,  # Set to True for SQL query debugging
            pool_pre_ping=True,  # Verify connections before using
        )

        # Enable foreign keys for SQLite
        if settings.database_url.startswith("sqlite"):
            @event.listens_for(self._engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

        logger.info("Database engine initialized successfully")

    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self._engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise

    def drop_tables(self):
        """Drop all database tables. USE WITH CAUTION!"""
        try:
            Base.metadata.drop_all(bind=self._engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Error dropping database tables: {e}")
            raise

    def get_session(self) -> Session:
        """
        Get a new database session.
        Caller is responsible for closing the session.
        """
        return self._session_factory()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope for database operations.
        Automatically commits on success, rolls back on error.

        Usage:
            with db.session_scope() as session:
                session.add(obj)
                # Automatic commit on success
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def dispose(self):
        """Dispose of the database engine and connection pool."""
        if self._engine:
            self._engine.dispose()
            logger.info("Database engine disposed")


# Global database instance
db = Database()


def init_database():
    """Initialize database and create tables."""
    logger.info("Initializing database...")
    db.create_tables()
    logger.info("Database initialization complete")


def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency injection function for database sessions.
    Use this in services that need database access.

    Usage:
        def my_service(session: Session = Depends(get_db_session)):
            result = session.query(Model).all()
    """
    session = db.get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
