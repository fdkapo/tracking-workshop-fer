"""Loading helpers for SkillCorner Open Data.

This file is COMPLETE. Read it as a worked example of a small, documented
module. You do not need to change it during the workshop.

Data source: https://github.com/SkillCorner/opendata (10 A-League 2024/25
matches). Please credit SkillCorner if you share work built on this data.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import pandas as pd
from kloppy import skillcorner

OPEN_DATA_URL = "https://raw.githubusercontent.com/SkillCorner/opendata/master/data"
DEFAULT_MATCH_ID = 1925299  # Brisbane Roar vs Perth Glory

MatchId = Union[int, str]


def _path(match_id: MatchId, suffix: str, data_dir: Optional[Union[str, Path]]) -> str:
    """Return a local path (if data_dir is given) or the GitHub raw URL for a match file."""
    name = f"{match_id}/{match_id}_{suffix}"
    if data_dir is not None:
        return str(Path(data_dir) / name)
    return f"{OPEN_DATA_URL}/matches/{name}"


def list_matches(data_dir: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """Return the 10 open-data matches as a tidy table (id, date, home, away)."""
    src = str(Path(data_dir) / "matches.json") if data_dir else f"{OPEN_DATA_URL}/matches.json"
    raw = pd.read_json(src)
    return pd.DataFrame(
        {
            "match_id": raw["id"],
            "date": pd.to_datetime(raw["date_time"]).dt.date,
            "home": raw["home_team"].map(lambda t: t["short_name"]),
            "away": raw["away_team"].map(lambda t: t["short_name"]),
        }
    ).sort_values("date", ignore_index=True)


def load_tracking(
    match_id: MatchId = DEFAULT_MATCH_ID,
    data_dir: Optional[Union[str, Path]] = None,
    **kwargs,
):
    """Load SkillCorner tracking data with kloppy.

    Returns a kloppy ``TrackingDataset``. Coordinates stay in SkillCorner's
    system: meters, origin at the center spot, x along the pitch length.

    Extra keyword arguments go straight to kloppy (e.g. ``limit=1000`` to load
    only the first 1000 frames while experimenting, or ``sample_rate=0.5``).
    """
    kwargs.setdefault("coordinates", "skillcorner")
    kwargs.setdefault("include_empty_frames", False)
    if data_dir is None:
        return skillcorner.load_open_data(match_id=str(match_id), **kwargs)
    return skillcorner.load(
        meta_data=_path(match_id, "match.json", data_dir),
        raw_data=_path(match_id, "tracking_extrapolated.jsonl", data_dir),
        **kwargs,
    )


def tracking_to_df(dataset) -> pd.DataFrame:
    """Convert a kloppy TrackingDataset to a wide pandas DataFrame.

    One row per frame. Columns: period_id, timestamp, frame_id, ball_x/y/z,
    then ``<player_id>_x`` and ``<player_id>_y`` for every player.
    """
    df = dataset.to_df(engine="pandas")
    # kloppy also adds <player_id>_d and _s columns (distance, speed); SkillCorner
    # does not fill them, so we drop them and compute our own in kinematics.py.
    drop = [c for c in df.columns if c.endswith("_d") or c.endswith("_s")]
    return df.drop(columns=drop).reset_index(drop=True)


def player_lookup(dataset) -> pd.DataFrame:
    """One row per player: id, name, number, position, team name, team id, home/away."""
    rows = []
    for team in dataset.metadata.teams:
        for p in team.players:
            rows.append(
                {
                    "player_id": int(p.player_id),
                    "name": p.name,
                    "number": p.jersey_no,
                    "position": str(p.starting_position) if p.starting_position else None,
                    "team": team.name,
                    "team_id": int(team.team_id),
                    "ground": str(team.ground),  # "home" or "away"
                }
            )
    return pd.DataFrame(rows)


def load_events(match_id: MatchId = DEFAULT_MATCH_ID, data_dir=None) -> pd.DataFrame:
    """Load SkillCorner dynamic events (one row per event, ~300 columns)."""
    return pd.read_csv(_path(match_id, "dynamic_events.csv", data_dir), low_memory=False)


def load_phases(match_id: MatchId = DEFAULT_MATCH_ID, data_dir=None) -> pd.DataFrame:
    """Load SkillCorner phases of play (one row per phase, with start/end frames)."""
    return pd.read_csv(_path(match_id, "phases_of_play.csv", data_dir))
