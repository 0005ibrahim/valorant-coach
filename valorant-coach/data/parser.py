"""
Turns raw val/match/v1 JSON into RoundEconomy / MatchSummary objects.

IMPORTANT: Riot's exact field names here are the part most likely to drift
between patches or to be slightly off from memory. Before trusting this,
run `python main.py --dump-raw` (see main.py) once and diff the printed
keys against the field names used below. This function is written against
the documented val/match/v1 schema as of early 2025:

  match["matchInfo"]["mapId"]
  match["players"][i] -> puuid, characterId (agent), teamId
  match["roundResults"][i] -> roundNum, winningTeam, plantPlayerId, defusePlayerId
  match["roundResults"][i]["playerStats"][j] -> puuid, kills, economy: {
        loadoutValue, weapon, armor, remaining, spent
  }

If Riot has changed field names since, this is the one function you'll
need to patch — everything downstream (storage, coach, dashboard) is
agnostic to the raw shape.
"""
from data.models import RoundEconomy, MatchSummary, classify_buy


def parse_match(raw: dict, target_puuid: str) -> MatchSummary:
    match_id = raw["matchInfo"]["matchId"]
    map_name = raw["matchInfo"].get("mapId", "unknown")

    # find the target player's team + agent
    player_info = next(p for p in raw["players"] if p["puuid"] == target_puuid)
    team_id = player_info["teamId"]
    agent = player_info.get("characterId", "unknown")

    rounds: list[RoundEconomy] = []

    for round_result in raw.get("roundResults", []):
        round_num = round_result["roundNum"] + 1  # Riot 0-indexes rounds
        winning_team = round_result.get("winningTeam")
        round_won = winning_team == team_id

        player_stat = next(
            (ps for ps in round_result.get("playerStats", []) if ps["puuid"] == target_puuid),
            None,
        )
        if player_stat is None:
            continue  # player data missing for this round (rare, but be defensive)

        economy = player_stat.get("economy", {})
        spent = economy.get("spent", 0)
        loadout_value = economy.get("loadoutValue", 0)
        remaining = economy.get("remaining", 0)

        kills = len(player_stat.get("kills", []))
        deaths = 1 if player_stat.get("wasKilled") else 0  # adjust if schema differs

        planted = round_result.get("plantPlayerId") == target_puuid
        defused = round_result.get("defusePlayerId") == target_puuid

        rounds.append(RoundEconomy(
            match_id=match_id,
            round_number=round_num,
            puuid=target_puuid,
            loadout_value=loadout_value,
            spent_credits=spent,
            remaining_credits=remaining,
            buy_type=classify_buy(spent, loadout_value),
            round_won=round_won,
            kills=kills,
            deaths=deaths,
            plant_or_defuse=planted or defused,
        ))

    won_rounds = sum(1 for r in rounds if r.round_won)
    lost_rounds = len(rounds) - won_rounds

    return MatchSummary(
        match_id=match_id,
        map_name=map_name,
        puuid=target_puuid,
        agent=agent,
        final_score_won=won_rounds,
        final_score_lost=lost_rounds,
        match_won=won_rounds > lost_rounds,
        rounds=rounds,
    )
