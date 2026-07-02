"""
Structured representations of match economy data.
Kept deliberately flat/simple so they map 1:1 onto SQLite rows and pandas rows.
"""
from dataclasses import dataclass
from enum import Enum


class BuyType(str, Enum):
    ECO = "eco"          # < 2000 spent
    FORCE = "force"       # 2000-3900 spent
    FULL = "full"           # 3900+ spent (full buy)
    SAVE = "save"             # < 1000 spent, no rifle/shotgun/smg/sniper/heavy


@dataclass
class RoundEconomy:
    match_id: str
    round_number: int          # 1-indexed
    puuid: str
    loadout_value: int          # total value of weapon + armor + abilities held
    spent_credits: int           # credits spent this round
    remaining_credits: int        # credits left after buying
    buy_type: BuyType
    round_won: bool
    kills: int
    deaths: int
    plant_or_defuse: bool          # did this player plant/defuse this round


@dataclass
class MatchSummary:
    match_id: str
    map_name: str
    puuid: str
    agent: str
    final_score_won: int
    final_score_lost: int
    match_won: bool
    rounds: list[RoundEconomy]


def classify_buy(spent_credits: int, loadout_value: int) -> BuyType:
    """
    Rough thresholds based on standard Valorant economy conventions.
    These are heuristics, not official Riot categories — tune against
    real data once you're looking at actual matches, buy behavior varies
    (e.g. a "force" with only a Spectre vs one with a Vandal look very different
    but both spend similarly).
    """
    if spent_credits >= 3900:
        return BuyType.FULL
    if spent_credits >= 2000:
        return BuyType.FORCE
    if spent_credits < 1000 and loadout_value < 1000:
        return BuyType.SAVE
    return BuyType.ECO
