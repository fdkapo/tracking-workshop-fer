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
    show_velocity: bool = True,
    arrow_seconds: float = 2.0,
):
    """Animate frames frame_start..frame_end. Returns a matplotlib FuncAnimation.

    Every player gets a velocity arrow pointing where they will be in
    ``arrow_seconds`` at their current velocity. The arrows come from
    ``kinematics.compute_kinematics``, so they are built on YOUR add_velocity.
    The runner (``highlight``) gets a gold arrow and a live label with speed,
    acceleration and direction from ``kinematics`` (its compute_kinematics output).

    Display in Jupyter with ``HTML(anim.to_jshtml())`` or save with
    ``anim.save("run.gif", writer=animation.PillowWriter(fps=10))``.
    """
    from src import kinematics as kin_mod  # local import: viz only needs it for arrows

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

    # Velocity for every player on the pitch, one array per frame: x, y, vx, vy.
    # quiver needs a fixed number of arrows, so players off the pitch get NaN (not drawn).
    arrow_ids = [i for i in home_ids + away_ids if f"{i}_x" in seq and seq[f"{i}_x"].notna().any()]
    vel = {}
    if show_velocity:
        for pid in arrow_ids + ([highlight] if highlight is not None else []):
            k = kin_mod.compute_kinematics(seq, pid).set_index("frame_id")
            vel[pid] = k[["x", "y", "vx", "vy"]]
    def vel_at(pids, f):
        """x, y, vx, vy for each player at frame f (zeros if unknown, so nothing is drawn)."""
        out = []
        for p in pids:
            r = vel[p].loc[f].to_numpy() if p in vel and f in vel[p].index else np.zeros(4)
            out.append(np.nan_to_num(r))
        return np.array(out).reshape(-1, 4)

    # quiver must start with real numbers (NaN at creation hides the arrows for good)
    f0 = seq["frame_id"].iloc[0]
    v0 = vel_at(arrow_ids, f0) if arrow_ids else np.zeros((1, 4))
    r0 = vel_at([highlight], f0) if highlight is not None else np.zeros((1, 4))
    scale = 1.0 / arrow_seconds  # quiver draws length = v / scale  ->  v * arrow_seconds meters
    arrows = ax.quiver(v0[:, 0], v0[:, 1], v0[:, 2], v0[:, 3], angles="xy", scale_units="xy", scale=scale,
                       color="#e6efea", width=0.003, zorder=4, alpha=0.9, visible=show_velocity)
    runner_arrow = ax.quiver(r0[:, 0], r0[:, 1], r0[:, 2], r0[:, 3], angles="xy", scale_units="xy",
                             scale=scale, color=HIGHLIGHT_COLOR, width=0.005, zorder=5,
                             visible=show_velocity and highlight is not None)
    stats = kinematics.set_index("frame_id") if kinematics is not None else None

    def update(i):
        row = seq.iloc[i]
        f = row["frame_id"]
        home.set_offsets(_team_xy(row, home_ids))
        away.set_offsets(_team_xy(row, away_ids))
        ball.set_offsets(np.array([[row["ball_x"], row["ball_y"]]]) if pd.notna(row["ball_x"]) else np.empty((0, 2)))
        if show_velocity and arrow_ids:
            v = vel_at(arrow_ids, f)
            arrows.set_offsets(v[:, :2])
            arrows.set_UVC(v[:, 2], v[:, 3])
        text = f"frame {int(f)}"
        if highlight is not None:
            runner.set_offsets(_team_xy(row, [highlight]))
            past = seq.iloc[max(0, i - trail): i + 1]
            trail_line.set_data(past[f"{highlight}_x"], past[f"{highlight}_y"])
            if show_velocity:
                r = vel_at([highlight], f)
                runner_arrow.set_offsets(r[:, :2])
                runner_arrow.set_UVC(r[:, 2], r[:, 3])
            if stats is not None and f in stats.index and pd.notna(stats.loc[f, "speed_kmh"]):
                s = stats.loc[f]
                text += f"   runner {s['speed_kmh']:.1f} km/h"
                if pd.notna(s.get("acceleration")):
                    text += f" · {s['acceleration']:+.1f} m/s²"
                if pd.notna(s.get("direction")):
                    text += f" · heading {s['direction']:.0f}°"
        label.set_text(text)
        return home, away, ball, arrows, runner, runner_arrow, trail_line, label

    anim = animation.FuncAnimation(fig, update, frames=len(seq), interval=1000 / fps, blit=True)
    plt.close(fig)  # stop Jupyter from also showing a static copy
    return anim
