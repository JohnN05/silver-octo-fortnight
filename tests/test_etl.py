import os
import datetime
from datetime import timezone
from unittest.mock import patch
import pytest

import database
import etl_pipeline
import config

@pytest.fixture
def db_conn():
    db_name = "test_etl.db"
    conn = database.initialize_db(db_name)
    yield conn
    conn.close()
    if os.path.exists(db_name):
        os.remove(db_name)

@pytest.fixture
def default_mocks():
    with patch("etl_pipeline.seatgeek_client.get_upcoming_edm_events") as mock_sg, \
         patch("etl_pipeline.ticketmaster_client.get_ticketmaster_event_details") as mock_tm, \
         patch("etl_pipeline.stubhub_scraper.scrape_stubhub_resale_price") as mock_stubhub, \
         patch("etl_pipeline.bootstrap_performer_history") as mock_bootstrap:
        
        mock_sg.return_value = [
            {
                "id": 12345,
                "title": "Fred again.. @ The Anthem",
                "artist": "Fred again..",
                "artist_id": 11111,
                "artist_score": 0.89,
                "date": "2026-09-02T20:00:00",
                "venue_name": "The Anthem",
                "venue_city": "Washington",
                "venue_state": "DC",
                "url": "https://seatgeek.com/fred-again-tickets"
            }
        ]
        mock_tm.return_value = {"face_value_min": 50.0, "onsale_date": "2026-01-01", "ticketmaster_url": "url"}
        mock_stubhub.return_value = 100.0
        
        def mock_bootstrap_impl(conn, performer_id, artist_name, score):
            perf_dict = {
                "id": performer_id,
                "name": artist_name,
                "popularity_score": score,
                "avg_past_markup": 120.0,
                "demand_rating": "HIGH"
            }
            database.save_performer(conn, perf_dict)
            shows = [
                {"performer_id": performer_id, "venue_name": "Space Miami", "venue_capacity": 2500, "date": "2026-01-20", "face_value": 50.0, "peak_resale": 135.0, "sell_out_days": 2.0}
            ]
            for s in shows:
                database.save_historical_show(conn, s)
                
        mock_bootstrap.side_effect = mock_bootstrap_impl
        
        yield mock_bootstrap, mock_stubhub, mock_tm, mock_sg

def test_etl_lazy_loading(default_mocks, db_conn):
    mock_bootstrap, mock_stubhub, mock_tm, mock_sg = default_mocks

    # Check clean database has no performers
    res = database.get_performer(db_conn, 11111)
    assert res is None
    
    # Run mock ETL
    etl_pipeline.run_daily_etl(db_conn)
    
    # Performer 11111 (mock Fred again..) should be populated
    perf = database.get_performer(db_conn, 11111)
    assert perf is not None
    assert len(database.get_historical_shows(db_conn, 11111)) > 0


def test_etl_fresh_cache(default_mocks, db_conn):
    mock_bootstrap, mock_stubhub, mock_tm, mock_sg = default_mocks
    
    # Add a fresh performer
    now = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    perf_dict = {
        "id": 11111,
        "name": "Fred again..",
        "popularity_score": 0.89,
        "avg_past_markup": 100.0,
        "demand_rating": "HIGH",
        "last_updated": now
    }
    database.save_performer(db_conn, perf_dict)
    
    # Check that it doesn't add historical shows because it's fresh
    res = etl_pipeline.run_daily_etl(db_conn)
    
    shows = database.get_historical_shows(db_conn, 11111)
    assert len(shows) == 0  # No new shows added
    mock_bootstrap.assert_not_called()

def test_etl_stale_cache(default_mocks, db_conn):
    mock_bootstrap, mock_stubhub, mock_tm, mock_sg = default_mocks
    
    # Add a stale performer
    stale_date = datetime.datetime.now(timezone.utc) - datetime.timedelta(days=config.STALE_THRESHOLD_DAYS + 2)
    perf_dict = {
        "id": 11111,
        "name": "Fred again..",
        "popularity_score": 0.89,
        "avg_past_markup": 100.0,
        "demand_rating": "HIGH"
    }
    database.save_performer(db_conn, perf_dict)
    
    # save_performer forces CURRENT_TIMESTAMP, so manually update to stale date
    cursor = db_conn.cursor()
    cursor.execute("UPDATE performers SET last_updated = ? WHERE id = ?", (stale_date.strftime("%Y-%m-%d %H:%M:%S"), 11111))
    db_conn.commit()
    
    # Should update because it's stale
    res = etl_pipeline.run_daily_etl(db_conn)
    
    shows = database.get_historical_shows(db_conn, 11111)
    assert len(shows) > 0  # Shows should be bootstrapped
    mock_bootstrap.assert_called_once()

