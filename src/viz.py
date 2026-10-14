"""Drawing tracking frames and animating sequences.

Workshop Part 4 (feature/frame-viz) and Part 5 (feature/animation).
"""
from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import animation
from mplsoccer import Pitch

HOME_COLOR = "#d62728"
AWAY_COLOR = "#1f77b4"
HIGHLIGHT_COLOR = "#ffbf00"
BALL_COLOR = "white"


def draw_pitch(pitch_length: float = 105, pitch_width: float = 68, ax=None):
    """Draw an empty pitch in SkillCorner coordinates. Returns (pitch, fig, ax)."""
    pitch = Pitch(
        pitch_type="skillcorner", pitch_length=pitch_length, pitch_width=pitch_width,
        pitch_color="#22312b", line_color="#c7d5cc",
    )
    if ax is None:
        fig, ax = pitch.draw(figsize=(10, 6.5))
    else:
        pitch.draw(ax=ax)
        fig = ax.figure
    return pitch, fig, ax


def _team_xy(row: pd.Series, ids) -> np.ndarray:
    pts = [(row.get(f"{i}_x"), row.get(f"{i}_y")) for i in ids]
    pts = [(x, y) for x, y in pts if pd.notna(x) and pd.notna(y)]
    return np.array(pts).reshape(-1, 2)


def plot_frame(
    tdf: pd.DataFrame,
    frame_id: int,
    players: pd.DataFrame,
    highlight=None,
    kinematics: Optional[pd.DataFrame] = None,
    pitch_length: float = 105,
    pitch_width: float = 68,
    ax=None,
    title: Optional[str] = None,
):
    """Plot every player and the ball at one frame.

    Args:
        tdf: wide tracking DataFrame (load.tracking_to_df).
        frame_id: the frame to draw.
        players: player lookup (load.player_lookup) with player_id and ground.
        highlight: player_id to draw in gold (e.g. the runner).
        kinematics: optional output of kinematics.compute_kinematics for the
            highlighted player; if given, a velocity arrow (1 s ahead) is drawn.
    Returns:
        (fig, ax)
    """
    row = tdf.loc[tdf["frame_id"] == frame_id]
    if row.empty:
        raise ValueError(f"frame {frame_id} not in tracking data")
    row = row.iloc[0]
    pitch, fig, ax = draw_pitch(pitch_length, pitch_width, ax)

    for ground, color in (("home", HOME_COLOR), ("away", AWAY_COLOR)):
        ids = players.loc[players["ground"] == ground, "player_id"]
        ids = [i for i in ids if i != highlight]
        xy = _team_xy(row, ids)
        pitch.scatter(xy[:, 0], xy[:, 1], s=180, c=color, edgecolors="white", linewidth=1, ax=ax, zorder=3, label=ground)

    if highlight is not None:
        hx, hy = row.get(f"{highlight}_x"), row.get(f"{highlight}_y")
        pitch.scatter(hx, hy, s=260, c=HIGHLIGHT_COLOR, edgecolors="black", linewidth=1.5, ax=ax, zorder=4, label="runner")
        if kinematics is not None:
            k = kinematics.loc[kinematics["frame_id"] == frame_id]
            if not k.empty and pd.notna(k["vx"].iloc[0]):
                pitch.arrows(hx, hy, hx + k["vx"].iloc[0], hy + k["vy"].iloc[0], width=2, color=HIGHLIGHT_COLOR, ax=ax, zorder=4)

    if pd.notna(row.get("ball_x")):
        pitch.scatter(row["ball_x"], row["ball_y"], s=70, c=BALL_COLOR, edgecolors="black", ax=ax, zorder=5, label="ball")

    ax.set_title(title or f"Frame {frame_id}", color="black")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.8)
    return fig, ax


def animate_sequence(
    tdf: pd.DataFrame,
    frame_start: int,
    frame_end: int,
    players: pd.DataFrame,
    highlight=None,
    kinematics: Optional[pd.DataFrame] = None,
    trail: int = 10,
    fps: int = 10,
    pitch_length: float = 105,
    pitch_width: float = 68,
):
    """Animate frames frame_start..frame_end. Returns a matplotlib FuncAnimation.

    Display in Jupyter with ``HTML(anim.to_jshtml())`` or save with
    ``anim.save("run.gif", writer=animation.PillowWriter(fps=10))``.
    """
    seq = tdf[(tdf["frame_id"] >= frame_start) & (tdf["frame_id"] <= frame_end)].reset_index(drop=True)
    if seq.empty:
        raise ValueError("no frames in that range")
    pitch, fig, ax = draw_pitch(pitch_length, pitch_width)

    home_ids = [i for i in players.loc[players["ground"] == "home", "player_id"] if i != highlight]
    away_ids = [i for i in players.loc[players["ground"] == "away", "player_id"] if i != highlight]
    home = ax.scatter([], [], s=180, c=HOME_COLOR, edgecolors="white", zorder=3)
    away = ax.scatter([], [], s=180, c=AWAY_COLOR, edgecolors="white", zorder=3)
    ball = ax.scatter([], [], s=70, c=BALL_COLOR, edgecolors="black", zorder=5)
    runner = ax.scatter([], [], s=260, c=HIGHLIGHT_COLOR, edgecolors="black", zorder=4)
    (trail_line,) = ax.plot([], [], color=HIGHLIGHT_COLOR, lw=2, alpha=0.7, zorder=3)
    label = ax.text(0.01, 0.98, "", transform=ax.transAxes, va="top", color="white", fontsize=11, zorder=6)
    speed = None
    if kinematics is not None:
        speed = kinematics.set_index("frame_id")["speed_kmh"]

    def update(i):
        row = seq.iloc[i]
        home.set_offsets(_team_xy(row, home_ids))
        away.set_offsets(_team_xy(row, away_ids))
        ball.set_offsets(np.array([[row["ball_x"], row["ball_y"]]]) if pd.notna(row["ball_x"]) else np.empty((0, 2)))
        text = f"frame {int(row['frame_id'])}"
        if highlight is not None:
            runner.set_offsets(_team_xy(row, [highlight]))
            past = seq.iloc[max(0, i - trail): i + 1]
            trail_line.set_data(past[f"{highlight}_x"], past[f"{highlight}_y"])
            if speed is not None and row["frame_id"] in speed.index and pd.notna(speed[row["frame_id"]]):
                text += f"   runner speed {speed[row['frame_id']]:.1f} km/h"
        label.set_text(text)
        return home, away, ball, runner, trail_line, label

    anim = animation.FuncAnimation(fig, update, frames=len(seq), interval=1000 / fps, blit=True)
    plt.close(fig)  # stop Jupyter from also showing a static copy
    return anim
