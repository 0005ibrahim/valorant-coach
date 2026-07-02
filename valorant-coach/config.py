"""
Central config. Loads .env, defines region routing, and shared constants.

Valorant uses "shard" routing (na/eu/ap/kr), which is different from the
platform routing (na1/euw1) you may have seen in League of Legends tutorials.
Account-v1 (Riot ID -> PUUID) uses a *continental* routing value instead
(americas/europe/asia), which is a separate axis from the shard. Both are
defined here so the rest of the code doesn't have to think about it.
"""
import os
from dotenv import load_dotenv

load_dotenv()

RIOT_API_KEY = os.getenv("RIOT_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not RIOT_API_KEY:
    raise RuntimeError("RIOT_API_KEY missing — copy .env.example to .env and fill it in")

# Valorant match/content shard routing (used for match-v5, val-content, etc.)
SHARD_ROUTING = {
    "na": "na",
    "eu": "eu",
    "ap": "ap",
    "kr": "kr",
    "latam": "na",   # latam and br currently route through na shard for match data
    "br": "na",
}

# account-v1 (Riot ID resolution) continental routing — separate from shard above
ACCOUNT_ROUTING = {
    "na": "americas",
    "latam": "americas",
    "br": "americas",
    "eu": "europe",
    "kr": "asia",
    "ap": "asia",
}

RIOT_API_BASE = "https://{routing}.api.riotgames.com"

# SQLite file location
DB_PATH = os.path.join(os.path.dirname(__file__), "valorant_coach.db")

# Anthropic model for coaching analysis
# Check https://docs.claude.com/en/docs/about-claude/models for the latest model IDs
CLAUDE_MODEL = "claude-sonnet-5"
