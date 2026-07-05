import database
import etl_pipeline

def test_etl_lazy_loading():
    # Verify that when etl runs on a new performer, it populates historical shows
    conn = database.initialize_db("test_etl.db")
    # Check clean database has no performers
    res = database.get_performer(conn, 11111)
    assert res is None
    
    # Run mock ETL
    etl_pipeline.run_daily_etl(conn, test_mode=True)
    
    # Performer 11111 (mock Fred again..) should be populated
    perf = database.get_performer(conn, 11111)
    assert perf is not None
    assert len(database.get_historical_shows(conn, 11111)) > 0
    
    conn.close()
    import os
    if os.path.exists("test_etl.db"):
        os.remove("test_etl.db")

def test_etl_fresh_cache():
    conn = database.initialize_db("test_etl_fresh.db")
    import datetime
    from datetime import timezone
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
    database.save_performer(conn, perf_dict)
    
    # Check that it doesn't add historical shows because it's fresh
    res = etl_pipeline.run_daily_etl(conn, test_mode=True)
    
    shows = database.get_historical_shows(conn, 11111)
    assert len(shows) == 0  # No new shows added
    
    conn.close()
    import os
    if os.path.exists("test_etl_fresh.db"):
        os.remove("test_etl_fresh.db")

def test_etl_stale_cache():
    conn = database.initialize_db("test_etl_stale.db")
    import datetime
    from datetime import timezone
    import config
    # Add a stale performer
    stale_date = datetime.datetime.now(timezone.utc) - datetime.timedelta(days=config.STALE_THRESHOLD_DAYS + 2)
    perf_dict = {
        "id": 11111,
        "name": "Fred again..",
        "popularity_score": 0.89,
        "avg_past_markup": 100.0,
        "demand_rating": "HIGH"
    }
    database.save_performer(conn, perf_dict)
    
    # save_performer forces CURRENT_TIMESTAMP, so manually update to stale date
    cursor = conn.cursor()
    cursor.execute("UPDATE performers SET last_updated = ? WHERE id = ?", (stale_date.strftime("%Y-%m-%d %H:%M:%S"), 11111))
    conn.commit()
    
    # Should update because it's stale
    res = etl_pipeline.run_daily_etl(conn, test_mode=True)
    
    shows = database.get_historical_shows(conn, 11111)
    assert len(shows) > 0  # Shows should be bootstrapped
    
    conn.close()
    import os
    if os.path.exists("test_etl_stale.db"):
        os.remove("test_etl_stale.db")

