import os
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Project root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.app.db.base import *  # noqa: F401,F403
from backend.app.db.database import Base
from backend.app.db.init_db import init_db


@pytest.fixture()
def knowledge_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "knowledge")
    )


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        from sqlalchemy import text

        conn.execute(
            text(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                    document_id UNINDEXED, title, content, tokenize='porter'
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS trg_documents_after_insert
                AFTER INSERT ON documents BEGIN
                    INSERT INTO documents_fts(document_id, title, content)
                    VALUES (new.id, new.title, new.content);
                END;
                """
            )
        )
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
