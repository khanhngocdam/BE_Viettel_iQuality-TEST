from app.db.session import SessionLocal, SessionSQLite

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def get_db_sqlite():
    db = SessionSQLite()
    try:
        yield db
    finally:
        db.close()
