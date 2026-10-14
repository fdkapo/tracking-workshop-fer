"""Drawing tracking frames and animating sequences.

Workshop Part 4 (feature/frame-viz): finish ``plot_frame``.
Workshop Part 5 (feature/animation): finish ``animate_sequence``.
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
    """Draw an empty pitch in SkillCorner coordinates. Returns (pitch, fig, ax). (Done.)"""
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
    """Return an (n, 2) array of x, y for the given player ids in one frame row,
    skipping players who are not on the pitch. (Done.)"""
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
            highlighted player; if given, draw a velocity arrow (where they will
            be in 1 second at their current velocity).
    Returns:
        (fig, ax)
    """
    row = tdf.loc[tdf["frame_id"] == frame_id]
    if row.empty:
        raise ValueError(f"frame {frame_id} not in tracking data")
    row = row.iloc[0]
    pitch, fig, ax = draw_pitch(pitch_length, pitch_width, ax)

    # TODO (Part 4) 1. Home and away players.
    #   For ground, color in (("home", HOME_COLOR), ("away", AWAY_COLOR)):
    #     - get that team's ids from `players` (leave out `highlight`)
    #     - xy = _team_xy(row, ids)
    #     - pitch.scatter(xy[:, 0], xy[:, 1], s=180, c=color, edgecolors="white", ax=ax, zorder=3, label=ground)

    # TODO (Part 4) 2. The highlighted player in HIGHLIGHT_COLOR (bigger, zorder=4).
    #   Bonus: if `kinematics` is given, find its row for this frame and draw
    #   pitch.arrows(x, y, x + vx, y + vy, width=2, color=HIGHLIGHT_COLOR, ax=ax)

    # TODO (Part 4) 3. The ball (ball_x, ball_y) in BALL_COLOR, only if it is not NaN.

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

    How FuncAnimation works: we create the artists (scatters, a line, a text)
    ONCE, empty. Then matplotlib calls ``update(i)`` for every frame i, and
    update only moves the existing artists with ``.set_offsets`` / ``.set_data``.
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
    speed = kinematics.set_index("frame_id")["speed_kmh"] if kinematics is not None else None

    def update(i):
        row = seq.iloc[i]
        # TODO (Part 5) 1. Move the players: home.set_offsets(_team_xy(row, home_ids)), same for away.
        # TODO (Part 5) 2. Move the ball: ball.set_offsets(np.array([[row["ball_x"], row["ball_y"]]]))
        #                  (use np.empty((0, 2)) when ball_x is NaN).
        text = f"frame {int(row['frame_id'])}"
        if highlight is not None:
            # TODO (Part 5) 3. Move the runner with _team_xy(row, [highlight]).
            # TODO (Part 5) 4. Trail: the runner's last `trail` positions,
            #                  past = seq.iloc[max(0, i - trail): i + 1]
            #                  trail_line.set_data(past[f"{highlight}_x"], past[f"{highlight}_y"])
            # TODO (Part 5) 5. Bonus: add the runner's speed (km/h) to `text` from `speed`.
            pass
        label.set_text(text)
        return home, away, ball, runner, trail_line, label

    anim = animation.FuncAnimation(fig, update, frames=len(seq), interval=1000 / fps, blit=True)
    plt.close(fig)  # stop Jupyter from also showing a static copy
    return anim
