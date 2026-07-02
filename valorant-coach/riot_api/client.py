"""
Thin wrapper around requests for Riot's API.

Handles:
- auth header
- basic 429 backoff (dev keys have low rate limits — 20/sec, 100/2min)
- raising clear errors instead of silently returning bad data
"""
import time
import requests
from config import RIOT_API_KEY, RIOT_API_BASE


class RiotAPIError(Exception):
    pass


class RiotClient:
    def __init__(self, max_retries: int = 3):
        self.session = requests.Session()
        self.session.headers.update({"X-Riot-Token": RIOT_API_KEY})
        self.max_retries = max_retries

    def get(self, routing: str, path: str, params: dict | None = None) -> dict:
        """
        routing: e.g. 'americas' (account-v1) or 'na' (match-v5 shard)
        path: e.g. '/riot/account/v1/accounts/by-riot-id/Name/TAG'
        """
        url = RIOT_API_BASE.format(routing=routing) + path
        attempt = 0

        while attempt <= self.max_retries:
            resp = self.session.get(url, params=params)

            if resp.status_code == 200:
                return resp.json()

            if resp.status_code == 429:
                # rate limited — respect Retry-After if present, else backoff
                wait = int(resp.headers.get("Retry-After", 2 ** attempt))
                time.sleep(wait)
                attempt += 1
                continue

            if resp.status_code == 401:
                raise RiotAPIError(
                    "401 Unauthorized — your RIOT_API_KEY is missing, wrong, or expired. "
                    "Dev keys expire every 24h; regenerate at developer.riotgames.com"
                )

            if resp.status_code == 404:
                raise RiotAPIError(f"404 Not Found — check the Riot ID / match ID is correct. URL: {url}")

            raise RiotAPIError(f"Riot API error {resp.status_code}: {resp.text[:300]}")

        raise RiotAPIError(f"Gave up after {self.max_retries} retries (rate limited). URL: {url}")
