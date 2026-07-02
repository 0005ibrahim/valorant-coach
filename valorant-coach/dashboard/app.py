"""
Streamlit dashboard. Reads from SQLite only — never calls Riot/Claude
directly. Run `python main.py` first to populate data.

    streamlit run dashboard/app.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.express as px
import streamlit as st

from data.storage import get_conn, init_db
from analysis.coach import get_coaching_feedback
from data.storage import get_rounds_for_puuid

st.set_page_config(page_title="Valorant Economy Coach", layout="wide")
init_db()

st.title("Valorant Economy Coach")

with get_conn() as conn:
    matches_df = pd.read_sql("SELECT * FROM matches ORDER BY pulled_at DESC", conn)
    rounds_df = pd.read_sql("SELECT * FROM rounds", conn)

if matches_df.empty:
    st.info("No data yet. Run `python main.py --riot-id \"Name#TAG\" --region na` first.")
    st.stop()

puuids = matches_df["puuid"].unique().tolist()
selected_puuid = st.selectbox("Player (puuid)", puuids)

player_matches = matches_df[matches_df["puuid"] == selected_puuid]
player_rounds = rounds_df[rounds_df["puuid"] == selected_puuid]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Matches tracked", len(player_matches))
col2.metric("Match win rate", f"{player_matches['match_won'].mean() * 100:.0f}%")

eco_rounds = player_rounds[player_rounds["buy_type"] == "eco"]
eco_win_rate = eco_rounds["round_won"].mean() * 100 if len(eco_rounds) else 0
col3.metric("Eco round win rate", f"{eco_win_rate:.0f}%")

force_rounds = player_rounds[player_rounds["buy_type"] == "force"]
force_win_rate = force_rounds["round_won"].mean() * 100 if len(force_rounds) else 0
col4.metric("Force-buy win rate", f"{force_win_rate:.0f}%")

st.subheader("Round win rate by buy type")
buy_summary = (
    player_rounds.groupby("buy_type")["round_won"]
    .agg(["mean", "count"])
    .rename(columns={"mean": "win_rate", "count": "rounds"})
    .reset_index()
)
buy_summary["win_rate"] = buy_summary["win_rate"] * 100
fig = px.bar(buy_summary, x="buy_type", y="win_rate", text="rounds",
             labels={"win_rate": "Win rate (%)", "buy_type": "Buy type"})
st.plotly_chart(fig, use_container_width=True)

st.subheader("Spend vs. loadout value over time")
fig2 = px.line(player_rounds.reset_index(), y=["spent_credits", "loadout_value"],
               labels={"value": "Credits", "index": "Round (chronological)"})
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Match history")
st.dataframe(
    player_matches[["map_name", "agent", "final_score_won", "final_score_lost", "match_won", "pulled_at"]],
    use_container_width=True,
)

st.subheader("Coaching feedback")
if st.button("Generate feedback"):
    with st.spinner("Asking Claude..."):
        rounds = get_rounds_for_puuid(selected_puuid)
        feedback = get_coaching_feedback(rounds)
    st.write(feedback)
