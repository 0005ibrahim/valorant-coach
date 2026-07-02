"""
Riot ID ("Name#TAG") -> PUUID -> list of recent match IDs -> full match JSON.

This is Valorant-specific (val/match/v1), not the League match-v5 endpoints
you'll see in most tutorials — the payload shape is different.
"""
from config import ACCOUNT_ROUTING, SHARD_ROUTING
from riot_api.client import RiotClient


class MatchResolver:
    def __init__(self):
        self.client = RiotClient()

    def get_puuid(self, riot_id: str, region: str) -> str:
        """riot_id like 'Sova Main#NA1'. region like 'na', 'eu', 'kr', 'ap'."""
        if "#" not in riot_id:
            raise ValueError("riot_id must be in 'Name#TAG' format, e.g. 'Sova Main#NA1'")
        name, tag = riot_id.split("#", 1)

        routing = ACCOUNT_ROUTING[region]
        data = self.client.get(
            routing,
            f"/riot/account/v1/accounts/by-riot-id/{name}/{tag}",
        )
        return data["puuid"]

    def get_recent_match_ids(self, puuid: str, region: str, count: int = 5) -> list[str]:
        shard = SHARD_ROUTING[region]
        data = self.client.get(
            shard,
            f"/val/match/v1/matchlists/by-puuid/{puuid}",
        )
        history = data.get("history", [])[:count]
        return [m["matchId"] for m in history]

    def get_match_details(self, match_id: str, region: str) -> dict:
        shard = SHARD_ROUTING[region]
        return self.client.get(shard, f"/val/match/v1/matches/{match_id}")
