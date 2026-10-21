"""Working with SkillCorner dynamic events and phases of play.

Workshop Part 2 (branch: feature/off-ball-runs).
YOUR TASK: implement ``get_off_ball_runs`` below. ``add_phase_info`` is done.
"""
from __future__ import annotations

from typing import Iterable, Optional, Union

import pandas as pd

RUN_COLUMNS = [
    "event_id", "period", "frame_start", "frame_end", "duration",
    "player_id", "player_name", "team_shortname", "event_subtype",
    "team_in_possession_phase_type", "x_start", "y_start", "x_end", "y_end",
    "distance_covered", "speed_avg", "targeted", "received", "dangerous",
    "lead_to_shot", "player_in_possession_id",
]


def add_phase_info(events: pd.DataFrame, phases: pd.DataFrame) -> pd.DataFrame:
    """Attach phase-of-play details to every event.

    Each event row has a ``phase_index`` that points at the ``index`` column of
    the phases table. We merge on it to bring in the phase's frame window,
    duration and whether the possession led to a shot.
    """
    cols = {
        "index": "phase_index",
        "frame_start": "phase_frame_start",
        "frame_end": "phase_frame_end",
        "duration": "phase_duration",
        "team_possession_lead_to_shot": "phase_lead_to_shot",
    }
    phase_cols = phases[list(cols)].rename(columns=cols)
    return events.merge(phase_cols, on="phase_index", how="left")


def _as_list(value: Union[str, Iterable[str], None]) -> Optional[list]:
    """Turn None -> None, "a" -> ["a"], ["a", "b"] -> ["a", "b"]."""
    if value is None:
        return None
    if isinstance(value, str):
        return [value]
    return list(value)


def get_off_ball_runs(
    events: pd.DataFrame,
    subtype: Union[str, Iterable[str], None] = None,
    phase: Union[str, Iterable[str], None] = None,
    targeted: Optional[bool] = None,
    min_duration: Optional[float] = None,
) -> pd.DataFrame:
    """Filter dynamic events down to off-ball runs.

    Args:
        events: the dynamic events table.
        subtype: one run type or a list, e.g. "behind" or ["overlap", "underlap"].
        phase: in-possession phase type(s), e.g. "create" or ["create", "finish"].
        targeted: if True/False, keep only runs that were (not) targeted by a pass.
        min_duration: keep runs lasting at least this many seconds.

    Returns:
        The matching runs, sorted by frame_start, with a fresh index (0, 1, 2...).

    Hints:
        - Start with rows where ``event_type == "off_ball_run"``.
        - Use ``_as_list`` so both "behind" and ["behind", "support"] work,
          then ``.isin(...)`` on ``event_subtype`` / ``team_in_possession_phase_type``.
        - Only apply a filter when its argument is not None.
        - Finish with ``.sort_values("frame_start").reset_index(drop=True)``.
    """
    # TODO (Part 2): replace the line below with your implementation
    #raise NotImplementedError("get_off_ball_runs is your Part 2 task")
    
    runs = events[events["event_type"] == "off_ball_run"]
    if subtype is not None:
        runs = runs[runs["event_subtype"].isin(_as_list(subtype))]
    if phase is not None:
        runs = runs[runs["team_in_possession_phase_type"].isin(_as_list(phase))]
    if targeted is not None:
        runs = runs[runs["targeted"] == targeted]
    if min_duration is not None:
        runs = runs[runs["duration"] >= min_duration]
    return runs.sort_values("frame_start").reset_index(drop=True)
