from sqlalchemy import text
from backend.app.db.database import engine, Base
# Import base to register all tables
from backend.app.db.base import *

def init_db():
    # 1. Create all SQLAlchemy standard tables
    Base.metadata.create_all(bind=engine)
    
    # 2. Setup SQLite specific FTS5 tables & triggers if running on SQLite
    # Check engine driver name
    if engine.url.drivername == "sqlite" or "sqlite" in engine.url.database:
        with engine.begin() as conn:
            # Create FTS5 virtual table
            conn.execute(text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                    document_id UNINDEXED,
                    title,
                    content,
                    tokenize='porter'
                );
            """))
            
            # Triggers to keep FTS table in sync with documents table
            # Insert Trigger
            conn.execute(text("""
                CREATE TRIGGER IF NOT EXISTS trg_documents_after_insert 
                AFTER INSERT ON documents 
                BEGIN
                    INSERT INTO documents_fts(document_id, title, content) 
                    VALUES (new.id, new.title, new.content);
                END;
            """))
            
            # Delete Trigger
            conn.execute(text("""
                CREATE TRIGGER IF NOT EXISTS trg_documents_after_delete 
                AFTER DELETE ON documents 
                BEGIN
                    DELETE FROM documents_fts WHERE document_id = old.id;
                END;
            """))
            
            # Update Trigger
            conn.execute(text("""
                CREATE TRIGGER IF NOT EXISTS trg_documents_after_update 
                AFTER UPDATE ON documents 
                BEGIN
                    UPDATE documents_fts 
                    SET title = new.title, content = new.content 
                    WHERE document_id = old.id;
                END;
            """))
            print("SQLite FTS5 virtual tables and sync triggers initialized successfully.")
