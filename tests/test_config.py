import os
import importlib
from unittest import mock

def test_config_variables_loaded():
    with mock.patch.dict(os.environ, {
        "TICKETMASTER_API_KEY": "test_tm_key",
        "SEATGEEK_CLIENT_ID": "test_sg_id",
        "DISCORD_WEBHOOK_URL": "http://test.url",
        "SCRAPER_API_KEY": "test_scraper_key",
        "EVENTBRITE_API_TOKEN": "test_eb_token",
    }):
        import config
        importlib.reload(config)
        assert config.TICKETMASTER_API_KEY == "test_tm_key"
        assert config.SCRAPER_API_KEY == "test_scraper_key"
        assert config.EVENTBRITE_API_TOKEN == "test_eb_token"
        assert config.STALE_THRESHOLD_DAYS == 7

def test_validate_config_no_ticketmaster_key():
    with mock.patch.dict(os.environ, {
        "SEATGEEK_CLIENT_ID": "test_sg_id",
        "DISCORD_WEBHOOK_URL": "http://test.url",
    }, clear=True):
        import config
        importlib.reload(config)
        # Should not include TICKETMASTER_API_KEY as missing
        missing = config.validate_config()
        assert "TICKETMASTER_API_KEY" not in missing
        assert len(missing) == 0
