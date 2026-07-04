import os
import pytest
import sqlite3
import database

@pytest.fixture
def db_conn():
    db_path = "test_edm_tracker_crud.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = database.initialize_db(db_path)
    yield conn
    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)

def test_db_initialization():
    db_path = "test_edm_tracker.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = database.initialize_db(db_path)
    assert os.path.exists(db_path)
    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)

def test_save_and_get_performer(db_conn):
    performer = {
        "id": 1,
        "name": "Skrillex",
        "popularity_score": 95.5,
        "avg_past_markup": 1.5,
        "demand_rating": "High"
    }
    saved_id = database.save_performer(db_conn, performer)
    assert saved_id == 1

    fetched = database.get_performer(db_conn, 1)
    assert fetched is not None
    assert fetched["name"] == "Skrillex"
    assert fetched["popularity_score"] == 95.5
    assert fetched["demand_rating"] == "High"
    assert fetched["avg_past_markup"] == 1.5

def test_get_performer_not_found(db_conn):
    fetched = database.get_performer(db_conn, 999)
    assert fetched is None

def test_save_event_foreign_key_error(db_conn):
    event = {
        "id": 100,
        "performer_id": 999, # doesn't exist
        "title": "Red Rocks Show",
        "venue_name": "Red Rocks",
        "date": "2023-10-10"
    }
    with pytest.raises(database.DatabaseError) as exc_info:
        database.save_event(db_conn, event)
    assert "FOREIGN KEY constraint failed" in str(exc_info.value) or "Error saving event" in str(exc_info.value)

def test_save_event_and_log_inventory(db_conn):
    performer = {
        "id": 2,
        "name": "Illenium",
        "popularity_score": 90.0
    }
    database.save_performer(db_conn, performer)
    
    event = {
        "id": 200,
        "performer_id": 2,
        "title": "Trilogy",
        "venue_name": "Allegiant Stadium",
        "date": "2024-02-02",
        "face_value": 150.0
    }
    database.save_event(db_conn, event)
    
    database.log_inventory(db_conn, 200, 500, 200.0)
    
    cursor = db_conn.cursor()
    cursor.execute("SELECT ticket_count, lowest_price FROM inventory_logs WHERE event_id = 200")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == 500
    assert row[1] == 200.0

def test_log_inventory_foreign_key_error(db_conn):
    with pytest.raises(database.DatabaseError):
        database.log_inventory(db_conn, 999, 100, 50.0) # event_id 999 doesn't exist

def test_historical_shows(db_conn):
    performer = {
        "id": 3,
        "name": "Odesza",
        "popularity_score": 92.0
    }
    database.save_performer(db_conn, performer)
    
    show = {
        "performer_id": 3,
        "venue_name": "Gorge",
        "venue_capacity": 27000,
        "date": "2023-07-04",
        "face_value": 89.5,
        "peak_resale": 250.0,
        "sell_out_days": 1.5
    }
    database.save_historical_show(db_conn, show)
    
    shows = database.get_historical_shows(db_conn, 3)
    assert len(shows) == 1
    assert shows[0]["venue_name"] == "Gorge"
    assert shows[0]["peak_resale"] == 250.0
    assert shows[0]["sell_out_days"] == 1.5

def test_save_historical_show_foreign_key_error(db_conn):
    show = {
        "performer_id": 999, # doesn't exist
        "venue_name": "Gorge",
        "date": "2023-07-04"
    }
    with pytest.raises(database.DatabaseError):
        database.save_historical_show(db_conn, show)
