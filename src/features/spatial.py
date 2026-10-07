"""Functions that get average spatial coordinates for reception and release events for a given match."""

import numpy as np  # noqa: F401
import pandas as pd

from src.database import get_matchevent_receptions, get_matchevent_releases
from src.features.normalise import get_normalised_y

OPEN_PLAY = ['Regular Play', 'From Keeper', 'From Counter', 'From Throw In']

def _tm_opreceptions(team_id : int, match_id : int, threads : int = 1):
    rec_df = get_matchevent_receptions(team_id, match_id, threads=threads)
    rec_df = get_normalised_y(rec_df)
    op_rec = rec_df[rec_df["play_pattern"].isin(OPEN_PLAY)]
    op_rec_grouped = op_rec.groupby("player_id").agg(
        team_id = ("team_id", "first"),
        match_id = ("match_id", "first"),
        player = ("player", "first"),
        position =("position", "first"),
        total_reception_events=("player_id", "size"),
        average_reception_x=("x", "mean"),
        average_reception_y=("y", "mean"),
    )
    return op_rec_grouped


def _tm_opreleases(team_id : int, match_id : int, threads : int = 1):
    rel_df = get_matchevent_releases(team_id, match_id, threads=threads)
    rel_df = get_normalised_y(rel_df)
    op_rel = rel_df[rel_df["play_pattern"].isin(OPEN_PLAY)]
    op_rel_grouped = op_rel.groupby("player_id").agg(
        total_release_events = ("player_id", "size"),
        average_release_x = ("x", "mean"),
        average_release_y=("y", "mean"),
    )
    return op_rel_grouped


def op_pm_avg_locations(team_id : int, match_id : int, threads : int = 1):
    return pd.concat([_tm_opreceptions(team_id, match_id, threads=threads), _tm_opreleases(team_id, match_id, threads=threads)], axis = 1)