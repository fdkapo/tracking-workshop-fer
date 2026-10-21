"""From positions to physics: speed, acceleration, direction and distances.

Workshop Part 3 (branch: feature/kinematics).
YOUR TASK: ``add_velocity``. Everything else is done; read it to see how it works.

All functions work on the wide tracking DataFrame from ``load.tracking_to_df``
(one row per frame, ``<player_id>_x`` / ``<player_id>_y`` columns) and on
SkillCorner coordinates (meters). Tracking runs at 10 frames per second.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

FPS = 10  # SkillCorner broadcast tracking: 10 frames per second


def player_xy(tdf: pd.DataFrame, player_id) -> pd.DataFrame:
    """Return a tidy frame_id / period_id / x / y table for one player."""
    pid = str(player_id)
    out = tdf[["frame_id", "period_id", f"{pid}_x", f"{pid}_y"]].copy()
    out.columns = ["frame_id", "period_id", "x", "y"]
    return out.reset_index(drop=True)


def smooth_positions(xy: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """Smooth x and y with a centered rolling mean.

    Raw tracking jitters by a few centimeters each frame. Differencing turns that
    jitter into huge fake speeds, so we smooth positions first.
    """
    out = xy.copy()
    for c in ("x", "y"):
        out[c] = out[c].rolling(window, center=True, min_periods=1).mean()
    return out


def add_velocity(xy: pd.DataFrame, fps: int = FPS) -> pd.DataFrame:
    """Add vx, vy (m/s), speed (m/s) and speed_kmh.   <-- YOUR TASK (Part 3)

    Hints:
        - Work on a copy: ``out = xy.copy()`` and return ``out``.
        - dt (seconds between rows) = ``out["frame_id"].diff() / fps``.
          Using frame numbers means a 3-frame gap correctly counts as 0.3 s.
        - vx = change in x / dt, vy = change in y / dt   (``.diff()``)
        - speed = sqrt(vx^2 + vy^2)  ->  ``np.hypot(vx, vy)``
        - speed_kmh = speed * 3.6
    """
    out = xy.copy()
    dt = out["frame_id"].diff() / fps
    out["vx"] = out["x"].diff() / dt
    out["vy"] = out["y"].diff() / dt
    out["speed"] = np.hypot(out["vx"], out["vy"])
    out["speed_kmh"] = out["speed"] * 3.6
    return out
    # TODO (Part 3): replace the line below with your implementation
    # raise NotImplementedError("add_velocity is your Part 3 task")


def add_acceleration(xy: pd.DataFrame, fps: int = FPS) -> pd.DataFrame:
    """Add acceleration (m/s^2): the change in speed per second. Needs ``speed``."""
    out = xy.copy()
    dt = out["frame_id"].diff() / fps
    out["acceleration"] = out["speed"].diff() / dt
    return out


def add_direction(xy: pd.DataFrame) -> pd.DataFrame:
    """Add direction in degrees: 0 = toward +x, 90 = toward +y. Needs vx, vy."""
    out = xy.copy()
    out["direction"] = np.degrees(np.arctan2(out["vy"], out["vx"]))
    return out


def compute_kinematics(tdf: pd.DataFrame, player_id, window: int = 5, fps: int = FPS) -> pd.DataFrame:
    """Run the full pipeline for one player: xy -> smooth -> velocity -> acceleration -> direction."""
    xy = smooth_positions(player_xy(tdf, player_id), window)
    return add_direction(add_acceleration(add_velocity(xy, fps), fps))


def distances_from_player(tdf: pd.DataFrame, player_id, other_ids: Iterable) -> pd.DataFrame:
    """Euclidean distance (m) from one player to each player in ``other_ids``, per frame.

    Returns a DataFrame indexed like ``tdf`` with one column per other player.
    Missing players (not on the pitch) give NaN.
    """
    pid = str(player_id)
    px, py = tdf[f"{pid}_x"].to_numpy(), tdf[f"{pid}_y"].to_numpy()
    cols = {}
    for oid in other_ids:
        oid = str(oid)
        if oid == pid or f"{oid}_x" not in tdf:
            continue
        cols[oid] = np.hypot(tdf[f"{oid}_x"].to_numpy() - px, tdf[f"{oid}_y"].to_numpy() - py)
    return pd.DataFrame(cols, index=tdf.index)


def nearest_opponent(tdf: pd.DataFrame, player_id, opponent_ids: Iterable) -> pd.DataFrame:
    """For each frame, the closest opponent's id and distance (m)."""
    d = distances_from_player(tdf, player_id, opponent_ids)
    arr = d.to_numpy(dtype=float)
    missing = np.isnan(arr).all(axis=1)  # frames where no opponent is tracked
    idx = np.argmin(np.where(np.isnan(arr), np.inf, arr), axis=1)
    ids = np.array(d.columns, dtype=object)[idx]
    ids[missing] = None
    dist = np.where(missing, np.nan, arr[np.arange(len(arr)), idx])
    return pd.DataFrame(
        {
            "frame_id": tdf["frame_id"].to_numpy(),
            "nearest_opponent_id": ids,
            "nearest_opponent_dist": dist,
        }
    )


def distance_to_ball(tdf: pd.DataFrame, player_id) -> pd.Series:
    """Distance (m) from a player to the ball, per frame (ball height ignored)."""
    pid = str(player_id)
    return np.hypot(tdf[f"{pid}_x"] - tdf["ball_x"], tdf[f"{pid}_y"] - tdf["ball_y"])
