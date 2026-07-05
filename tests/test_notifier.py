import os
import pytest
import notifier
import config

def test_concise_embeds():
    event = {
        "artist": "Fred again..",
        "venue": "The Anthem",
        "date": "2026-09-02T20:00:00",
        "face_value": 75.0,
        "resale_lowest": 220.0,
        "url": "https://seatgeek.com/fred-again",
        "venue_city": "Washington"
    }
    analysis = {
        "priority_score": 85.0,
        "rating": "CRITICAL",
        "roi": 149.0
    }
    # Validate report formatting logic
    report_md = notifier.generate_markdown_report([(event, analysis)])
    assert "Fred again.." in report_md
    assert "CRITICAL" in report_md

def test_missing_resale_lowest():
    event = {
        "artist": "Local DJ",
        "venue": "Soundcheck",
        "date": "2026-10-01T22:00:00",
        "face_value": 30.0,
        "url": "https://seatgeek.com/local-dj",
        "venue_city": "Washington"
    }
    analysis = {
        "priority_score": 50.0,
        "rating": "STANDARD",
        "roi": 0.0
    }
    report_md = notifier.generate_markdown_report([(event, analysis)])
    assert "Local DJ" in report_md
    assert "0.00" in report_md # Resale lowest should default to 0.00 in report
    
def test_empty_events():
    report_md = notifier.generate_markdown_report([])
    assert "High-Priority Upcoming Opportunities" in report_md
    assert "Fred again.." not in report_md

def test_discord_notification_success(requests_mock):
    config.DISCORD_WEBHOOK_URL = "http://test-webhook.com"
    requests_mock.post("http://test-webhook.com", status_code=204)
    
    event = {
        "artist": "Fred again..",
        "venue": "The Anthem",
        "date": "2026-09-02T20:00:00",
        "face_value": 75.0,
        "resale_lowest": 220.0,
        "url": "https://seatgeek.com/fred-again",
        "venue_city": "Washington"
    }
    analysis = {
        "priority_score": 85.0,
        "rating": "CRITICAL",
        "roi": 149.0
    }
    
    success = notifier.send_discord_notification([(event, analysis)])
    assert success is True
    assert requests_mock.called

def test_discord_notification_missing_webhook():
    config.DISCORD_WEBHOOK_URL = ""
    success = notifier.send_discord_notification([])
    assert success is False

def test_discord_notification_empty_events(requests_mock):
    config.DISCORD_WEBHOOK_URL = "http://test-webhook.com"
    success = notifier.send_discord_notification([])
    assert success is True
    assert not requests_mock.called

def test_discord_notification_est_resale(requests_mock):
    config.DISCORD_WEBHOOK_URL = "http://test-webhook.com"
    requests_mock.post("http://test-webhook.com", status_code=200)
    
    event = {
        "artist": "Fred again..",
        "venue": "The Anthem",
        "date": "2026-09-02T20:00:00",
        "face_value": 75.0,
        "avg_past_markup": 1.5,
        "url": "https://seatgeek.com/fred-again",
        "venue_city": "Washington"
    }
    analysis = {
        "priority_score": 85.0,
        "rating": "CRITICAL",
        "roi": 149.0
    }
    
    success = notifier.send_discord_notification([(event, analysis)])
    assert success is True
    assert requests_mock.called
    history = requests_mock.request_history
    assert "Estimated Resale Value: $187.50" in history[0].json()["embeds"][1]["description"]

def test_discord_notification_network_failure(requests_mock):
    import requests
    config.DISCORD_WEBHOOK_URL = "http://test-webhook.com"
    requests_mock.post("http://test-webhook.com", exc=requests.exceptions.RequestException("Network down"))
    
    event = {
        "artist": "Fred again..",
        "venue": "The Anthem",
        "face_value": 75.0,
        "url": "https://seatgeek.com/fred-again"
    }
    analysis = {
        "priority_score": 85.0,
        "rating": "CRITICAL",
        "roi": 149.0
    }
    
    success = notifier.send_discord_notification([(event, analysis)])
    assert success is False
    assert requests_mock.called
