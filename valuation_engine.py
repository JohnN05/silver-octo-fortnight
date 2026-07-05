from datetime import datetime

def compute_score(event):
    face_val = event.get("face_value", 50.0)
    resale_lowest = event.get("resale_lowest")
    
    # 1. Markup / ROI Score (40% weight)
    if resale_lowest:
        roi = ((resale_lowest - face_val - (resale_lowest * 0.15)) / face_val) * 100.0
        markup_score = min(max(roi / 1.5, 0.0), 100.0) # ROI >= 150% gets 100 points
    else:
        roi = 0.0
        markup_score = 0.0
        
    # 2. Sales Velocity Score (30% weight)
    velocity = event.get("velocity", 0.0) # percentage drop in inventory daily
    velocity_score = min(velocity * 4.0, 100.0) # 25% daily reduction gets 100 points
    
    # 3. Historical Score (30% weight)
    avg_past_markup = event.get("avg_past_markup", 0.0)
    sell_out_days = event.get("sell_out_days", 14.0)
    
    hist_markup_points = min(avg_past_markup / 1.5, 50.0) # +150% gets 50 points
    hist_sell_points = max(50.0 - (sell_out_days * 3.5), 0.0) # immediate sell-out gets 50 points
    hist_score = hist_markup_points + hist_sell_points
    
    # Total priority score
    priority_score = (0.40 * markup_score) + (0.30 * velocity_score) + (0.30 * hist_score)
    
    if priority_score >= 75.0:
        rating = "CRITICAL"
    elif priority_score >= 50.0:
        rating = "HIGH"
    elif priority_score >= 25.0:
        rating = "MEDIUM"
    else:
        rating = "LOW"
        
    return {
        "priority_score": round(priority_score, 1),
        "rating": rating,
        "roi": round(roi, 1)
    }

def calculate_event_velocity(conn, event_id):
    cursor = conn.cursor()
    # Retrieve the last 2 logs to calculate daily drop
    cursor.execute("""
        SELECT ticket_count, check_time FROM inventory_logs 
        WHERE event_id = ? ORDER BY check_time DESC LIMIT 2
    """, (event_id,))
    rows = cursor.fetchall()
    if len(rows) < 2:
        return 0.0
    
    count_latest, time_latest = rows[0]
    count_prev, time_prev = rows[1]
    
    if count_prev == 0 or count_latest is None or count_prev is None:
        return 0.0
    
    try:
        t_latest = datetime.fromisoformat(str(time_latest).replace("Z", "+00:00"))
        t_prev = datetime.fromisoformat(str(time_prev).replace("Z", "+00:00"))
        time_diff = (t_latest - t_prev).total_seconds()
    except (ValueError, TypeError):
        time_diff = 86400.0
        
    if time_diff <= 0:
        time_diff = 86400.0
    
    # Calculate % change
    diff = count_prev - count_latest
    if diff <= 0:
        return 0.0
        
    percentage_reduction = (diff / count_prev) * 100.0
    daily_velocity = percentage_reduction * (86400.0 / time_diff)
    return daily_velocity

def calculate_priority_score(conn, event: dict) -> dict:
    event_id = event.get("event_id")
    if event_id and conn:
        event["velocity"] = calculate_event_velocity(conn, event_id)
    
    score_data = compute_score(event)
    event.update(score_data)
    return event

def estimate_face_value(artist_score: float) -> float:
    # A simple estimation: higher popularity = higher face value
    if artist_score > 0.8:
        return 75.0
    elif artist_score > 0.6:
        return 55.0
    else:
        return 40.0

