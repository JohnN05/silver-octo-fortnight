import os
import database

def test_db_initialization():
    db_path = "test_edm_tracker.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = database.initialize_db(db_path)
    assert os.path.exists(db_path)
    conn.close()
    os.remove(db_path)
