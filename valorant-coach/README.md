# Valorant Economy Coach

Pulls match data from Riot's API, extracts round-by-round economy decisions,
stores it, and uses Claude to generate plain-English coaching feedback.
Dashboard displays trends over time.

## Project structure

```
valorant-coach/
├── config.py                # env vars, region routing, constants
├── riot_api/
│   ├── client.py             # low-level HTTP client (rate limiting, headers)
│   └── resolver.py           # Riot ID -> PUUID -> match ID list
├── data/
│   ├── models.py              # dataclasses: RoundEconomy, MatchSummary
│   ├── parser.py               # raw Riot JSON -> structured round data
│   └── storage.py               # SQLite read/write
├── analysis/
│   └── coach.py                   # sends round data to Claude, returns insights
├── dashboard/
│   └── app.py                      # Streamlit UI reading from SQLite
├── main.py                          # CLI: orchestrates the full pipeline
├── requirements.txt
└── .env.example
```

## Setup

```bash
cd valorant-coach
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in your keys
```

You need two keys in `.env`:
- `RIOT_API_KEY` — from https://developer.riotgames.com/ (temp key expires in 24h during dev)
- `ANTHROPIC_API_KEY` — from https://console.anthropic.com/

## Usage

```bash
# Pull a match, parse economy, store it, get Claude's analysis
python main.py --riot-id "YourName#TAG" --region na

# Launch the dashboard
streamlit run dashboard/app.py
```

## Build order (recommended)

1. `riot_api/client.py` + `resolver.py` — confirm you can actually pull a match. Print raw JSON, look at it.
2. `data/parser.py` — turn that JSON into round-by-round economy rows. Print the table, sanity check it against your own memory of the game.
3. `data/storage.py` — persist it so you're not re-pulling every run.
4. `analysis/coach.py` — feed stored rounds to Claude, read the output.
5. `dashboard/app.py` — only once 1–4 work from the command line.

Don't start the dashboard until `main.py` runs cleanly end to end in the terminal.
This is a hard rule for this project specifically — a UI on top of broken data
just hides the bug.

## Known gotchas

- Valorant API routing uses shard clusters (`na`, `eu`, `ap`, `kr`), not the
  platform IDs (`na1`, `euw1`) you may have seen in League tutorials.
- Riot's match-v5 payload structure differs between MOBA and Valorant — this
  code targets the Valorant match-details schema specifically.
- Temp dev keys expire every 24 hours. If you get 401s, regenerate it.
- Rate limit on dev keys is low (20 req/sec, 100 req/2min). The client below
  handles basic backoff but don't hammer it in a loop over many matches yet.
