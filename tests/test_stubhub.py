import stubhub_scraper
import pytest
import requests

def test_stubhub_url_sanitization():
    url = stubhub_scraper.get_stubhub_search_url("Fred again..", "Washington DC")
    # Expect dots to be stripped and secure search path used
    assert ".." not in url
    assert "secure/search" in url
    assert "Fred%20again" in url

def test_scrape_stubhub_resale_price_initial_state(requests_mock):
    url = stubhub_scraper.get_stubhub_search_url("Martin Garrix", "Washington DC")
    requests_mock.get(url, text='<html><body><script>window.__INITIAL_STATE__ = {"minPrice": 85.50}</script></body></html>')
    price = stubhub_scraper.scrape_stubhub_resale_price("Martin Garrix", "Washington DC")
    assert price == 85.50

def test_scrape_stubhub_resale_price_regex(requests_mock):
    url = stubhub_scraper.get_stubhub_search_url("Martin Garrix", "Washington DC")
    requests_mock.get(url, text='<html><body><div>Tickets from $90 and up</div></body></html>')
    price = stubhub_scraper.scrape_stubhub_resale_price("Martin Garrix", "Washington DC")
    assert price == 90.0

def test_scrape_stubhub_resale_price_403(requests_mock):
    url = stubhub_scraper.get_stubhub_search_url("Martin Garrix", "Washington DC")
    requests_mock.get(url, status_code=403)
    price = stubhub_scraper.scrape_stubhub_resale_price("Martin Garrix", "Washington DC")
    assert price is None

def test_scrape_stubhub_resale_price_non_200(requests_mock):
    url = stubhub_scraper.get_stubhub_search_url("Martin Garrix", "Washington DC")
    requests_mock.get(url, status_code=500)
    price = stubhub_scraper.scrape_stubhub_resale_price("Martin Garrix", "Washington DC")
    assert price is None

def test_scrape_stubhub_resale_price_exception(requests_mock):
    url = stubhub_scraper.get_stubhub_search_url("Martin Garrix", "Washington DC")
    requests_mock.get(url, exc=requests.exceptions.ConnectTimeout)
    price = stubhub_scraper.scrape_stubhub_resale_price("Martin Garrix", "Washington DC")
    assert price is None
