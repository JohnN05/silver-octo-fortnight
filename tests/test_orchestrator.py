import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
import orchestrator

def test_is_stale():
    # Test missing date
    assert orchestrator.is_stale(None, 7) == True
    
    # Test valid date, not stale
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
    assert orchestrator.is_stale(recent, 7) == False
    
    # Test stale date
    stale = (now - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S")
    assert orchestrator.is_stale(stale, 7) == True

@patch("database.get_performer")
@patch("database.save_performer")
@patch("seatgeek_client.get_performer_resale_average")
def test_get_or_update_performer_cached(mock_avg, mock_save, mock_get):
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
    
    mock_get.return_value = {
        "id": 123,
        "name": "Test Artist",
        "last_updated": recent
    }
    
    conn = MagicMock()
    result = orchestrator.get_or_update_performer(conn, 123, "Test Artist", 0.8)
    
    # Should use cache, so it shouldn't call seatgeek or save_performer
    mock_avg.assert_not_called()
    mock_save.assert_not_called()
    assert result["id"] == 123

@patch("database.get_performer")
@patch("database.save_performer")
@patch("seatgeek_client.get_performer_resale_average")
def test_get_or_update_performer_stale(mock_avg, mock_save, mock_get):
    now = datetime.now(timezone.utc)
    stale = (now - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S")
    
    # First call returns stale, second call returns updated
    mock_get.side_effect = [
        {"id": 123, "name": "Test Artist", "last_updated": stale},
        {"id": 123, "name": "Test Artist", "last_updated": now.strftime("%Y-%m-%d %H:%M:%S")}
    ]
    mock_avg.return_value = 150.0
    
    conn = MagicMock()
    result = orchestrator.get_or_update_performer(conn, 123, "Test Artist", 0.8)
    
    # Should fetch and update cache
    mock_avg.assert_called_once_with(123)
    mock_save.assert_called_once()
    
@patch("ticketmaster_client.get_ticketmaster_event_details")
@patch("resale_checker.estimate_face_value")
@patch("database.save_event")
@patch("orchestrator.get_or_update_performer")
def test_process_event_tm_fallback(mock_get_perf, mock_save_event, mock_estimate, mock_tm):
    # Case 1: TM provides face value
    mock_tm.return_value = {"face_value_min": 60.0, "ticketmaster_url": "tm_url", "onsale_date": "date"}
    event = {"artist": "Artist", "artist_id": 1, "artist_score": 0.8, "venue_city": "DC"}
    conn = MagicMock()
    
    result = orchestrator.process_event(conn, dict(event))
    assert result["face_value"] == 60.0
    mock_estimate.assert_not_called()
    
    # Case 2: TM does not provide face value
    mock_tm.return_value = {"ticketmaster_url": "tm_url"}
    mock_estimate.return_value = 75.0
    
    result = orchestrator.process_event(conn, dict(event))
    assert result["face_value"] == 75.0
    mock_estimate.assert_called_once_with(0.8, None)
    
    # Case 3: TM returns None completely
    mock_tm.return_value = None
    mock_estimate.reset_mock()
    
    result = orchestrator.process_event(conn, dict(event))
    assert result["face_value"] == 75.0
    mock_estimate.assert_called_once_with(0.8, None)
