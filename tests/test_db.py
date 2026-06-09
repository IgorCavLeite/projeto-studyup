import os
from backend.database import connection


def test_init_db(tmp_path):
    db = tmp_path / "test.db"
    connection.DB_PATH = str(db)
    if db.exists():
        os.remove(db)
    connection.init_db()
    assert db.exists()
