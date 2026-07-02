"""
Sends structured round-economy data to Claude and gets back plain-English
coaching feedback. This is the "why" layer sitting on top of the "what
happened" data from Riot's API.
"""
import json
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from data.models import RoundEconomy

SYSTEM_PROMPT = """You are a Valorant economy coach. You'll be given a
player's round-by-round economy data across one or more matches: buy type,
credits spent, loadout value, whether the round was won, kills/deaths, and
whether they planted/defused.

Identify concrete, specific patterns — not generic advice. Good examples:
"You force-bought on 6 of 8 pistol-round losses, going 1-5 in those rounds"
or "Your eco rounds have a 40% win rate, well above average, but you're
only eco-ing 2000 credits below the force-buy threshold — you likely have
room to save more aggressively."

Bad output: generic tips like "manage your economy better" or "play safer
on eco rounds" without tying it to their actual numbers.

Return exactly 3 findings, each 1-3 sentences, ordered by impact. Return
plain text, no markdown headers, no preamble."""


def get_coaching_feedback(rounds: list[RoundEconomy]) -> str:
    if not rounds:
        return "No round data available yet — pull at least one match first."

    payload = [
        {
            "match_id": r.match_id,
            "round": r.round_number,
            "buy_type": r.buy_type.value,
            "spent": r.spent_credits,
            "loadout_value": r.loadout_value,
            "remaining": r.remaining_credits,
            "won": r.round_won,
            "kills": r.kills,
            "deaths": r.deaths,
            "plant_or_defuse": r.plant_or_defuse,
        }
        for r in rounds
    ]

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Round data:\n{json.dumps(payload, indent=2)}"}
        ],
    )

    return "".join(block.text for block in response.content if block.type == "text")
