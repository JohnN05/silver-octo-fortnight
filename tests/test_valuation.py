import sqlite3
import pytest
import valuation_engine

def test_priority_score_calculation():
    # High markup, high velocity, strong historical stats
    event = {
        "artist_score": 0.85,
        "face_value": 50.0,
        "resale_lowest": 150.0,
        "avg_past_markup": 120.0,
        "sell_out_days": 1.0,
        "velocity": 25.0 # percentage inventory reduction
    }
    res = valuation_engine.compute_score(event)
    assert res["priority_score"] >= 75
    assert res["rating"] == "CRITICAL"

def test_compute_score_missing_parameters():
    event = {}
    res = valuation_engine.compute_score(event)
    assert res["rating"] in ["LOW", "MEDIUM"]
    assert res["roi"] == 0.0

def test_compute_score_low_demand():
    event = {
        "face_value": 100.0,
        "resale_lowest": 80.0, # Selling below face value
        "velocity": 0.0,
        "avg_past_markup": -10.0,
        "sell_out_days": 60.0
    }
    res = valuation_engine.compute_score(event)
    assert res["priority_score"] < 25.0
    assert res["rating"] == "LOW"
    assert res["roi"] < 0.0

def test_compute_score_high_demand():
    event = {
        "face_value": 30.0,
        "resale_lowest": 150.0,
        "velocity": 50.0, # 50% drop daily
        "avg_past_markup": 200.0,
        "sell_out_days": 0.0 # Sold out immediately
    }
    res = valuation_engine.compute_score(event)
    assert res["priority_score"] >= 75.0
    assert res["rating"] == "CRITICAL"

def setup_db():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE inventory_logs (
            id INTEGER PRIMARY KEY,
            event_id TEXT,
            ticket_count INTEGER,
            check_time TEXT
        )
    """)
    conn.commit()
    return conn

def test_calculate_event_velocity_normal():
    conn = setup_db()
    cursor = conn.cursor()
    # Insert older log first, then newer log
    cursor.execute("INSERT INTO inventory_logs (event_id, ticket_count, check_time) VALUES ('E1', 100, '2023-01-01T10:00:00Z')")
    cursor.execute("INSERT INTO inventory_logs (event_id, ticket_count, check_time) VALUES ('E1', 75, '2023-01-02T10:00:00Z')")
    conn.commit()
    
    velocity = valuation_engine.calculate_event_velocity(conn, 'E1')
    assert velocity == 25.0

def test_calculate_event_velocity_insufficient_logs():
    conn = setup_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO inventory_logs (event_id, ticket_count, check_time) VALUES ('E1', 100, '2023-01-01T10:00:00Z')")
    conn.commit()
    
    velocity = valuation_engine.calculate_event_velocity(conn, 'E1')
    assert velocity == 0.0

def test_calculate_event_velocity_no_logs():
    conn = setup_db()
    velocity = valuation_engine.calculate_event_velocity(conn, 'E1')
    assert velocity == 0.0

def test_calculate_event_velocity_increase_inventory():
    conn = setup_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO inventory_logs (event_id, ticket_count, check_time) VALUES ('E1', 100, '2023-01-01T10:00:00Z')")
    cursor.execute("INSERT INTO inventory_logs (event_id, ticket_count, check_time) VALUES ('E1', 110, '2023-01-02T10:00:00Z')")
    conn.commit()
    
    velocity = valuation_engine.calculate_event_velocity(conn, 'E1')
    assert velocity == 0.0

def test_calculate_event_velocity_zero_prev():
    conn = setup_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO inventory_logs (event_id, ticket_count, check_time) VALUES ('E1', 0, '2023-01-01T10:00:00Z')")
    cursor.execute("INSERT INTO inventory_logs (event_id, ticket_count, check_time) VALUES ('E1', 0, '2023-01-02T10:00:00Z')")
    conn.commit()
    
    velocity = valuation_engine.calculate_event_velocity(conn, 'E1')
    assert velocity == 0.0
