"""Curve plotting (optional matplotlib backend).

Importing this module fails fast with a friendly error message if matplotlib
is not installed. Install via the optional extra: ``pip install curveforge[plot]``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from curveforge.curve import Curve

try:
    import matplotlib.pyplot as plt
except ImportError as exc:  # pragma: no cover — exercised only without matplotlib
    msg = "matplotlib is required for plotting. Install it with: pip install 'curveforge[plot]'"
    raise ImportError(msg) from exc


_DEFAULT_FREQ_RANGE: tuple[float, float] = (10.0, 20000.0)
_DEFAULT_GAIN_RANGE: tuple[float, float] = (-8.0, 14.0)
_FIG_SIZE: tuple[float, float] = (12.0, 5.5)
_DPI: int = 150

# Curated palette: distinct hues at sensible saturation, tested against
# white backgrounds (README rendered on GitHub).
# curveforge: allow-literal
_PALETTE: tuple[str, ...] = (
    "#2E5EAA",  # deep blue
    "#D17A22",  # orange
    "#3E8E5A",  # forest green
    "#C0394C",  # crimson
    "#7A52A6",  # purple
    "#B8860B",  # dark goldenrod
    "#0F8B8D",  # teal
    "#7F7F7F",  # grey
)

# Octave anchor frequencies marked subtly on the x-axis for visual reference.
_OCTAVE_ANCHORS: tuple[float, ...] = (20.0, 100.0, 1000.0, 10000.0)

# Clean human-readable tick labels on the log frequency axis.
_TICK_FREQS: tuple[int, ...] = (20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000)
_TICK_LABELS: tuple[str, ...] = ("20", "50", "100", "200", "500", "1k", "2k", "5k", "10k", "20k")


def plot_curve(curve: Curve, title: str, *, subtitle: str | None = None) -> Figure:
    """Render a single curve as a magnitude response plot."""
    fig, ax = plt.subplots(figsize=_FIG_SIZE, dpi=_DPI)
    ax.semilogx(curve.freqs, curve.gains_db, color=_PALETTE[0], linewidth=2.4)
    _style_axes(ax, title=title, subtitle=subtitle)
    fig.tight_layout()
    return fig


def plot_overlay(
    curves: list[tuple[str, Curve]],
    *,
    title: str = "Curve comparison",
    subtitle: str | None = None,
) -> Figure:
    """Render multiple curves overlaid on the same axes."""
    fig, ax = plt.subplots(figsize=_FIG_SIZE, dpi=_DPI)
    for index, (label, curve) in enumerate(curves):
        ax.semilogx(
            curve.freqs,
            curve.gains_db,
            color=_PALETTE[index % len(_PALETTE)],
            linewidth=2.2,
            label=label,
        )
    _style_axes(ax, title=title, subtitle=subtitle)
    legend = ax.legend(
        loc="upper right",
        fontsize=9,
        framealpha=0.92,
        edgecolor="#cccccc",
        fancybox=False,
    )
    legend.get_frame().set_linewidth(0.5)
    fig.tight_layout()
    return fig


def save_figure(fig: Figure, path: Path) -> None:
    """Save a Figure to disk; format inferred from extension. Always 150 DPI for PNG."""
    fig.savefig(path, dpi=_DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def show_figure(fig: Figure) -> None:
    """Show a Figure in an interactive window (blocks until closed)."""
    plt.show()
    plt.close(fig)


def _style_axes(ax: Axes, title: str, subtitle: str | None) -> None:
    _set_title_block(ax, title=title, subtitle=subtitle)
    ax.set_xlabel("Frequency (Hz)", fontsize=10, color="#444444")
    ax.set_ylabel("Gain (dB)", fontsize=10, color="#444444")
    ax.set_xlim(_DEFAULT_FREQ_RANGE)
    ax.set_ylim(_DEFAULT_GAIN_RANGE)
    _style_grid_and_spines(ax)
    ax.set_xticks(list(_TICK_FREQS))
    ax.set_xticklabels(list(_TICK_LABELS))
    ax.tick_params(axis="both", labelsize=9, colors="#444444")
    ax.axhline(y=0.0, color="#888888", linewidth=0.7, alpha=0.5, zorder=1)
    for freq in _OCTAVE_ANCHORS:
        ax.axvline(x=freq, color="#cccccc", linewidth=0.5, alpha=0.6, zorder=0)


def _set_title_block(ax: Axes, title: str, subtitle: str | None) -> None:
    if subtitle is not None:
        ax.set_title(title, fontsize=13, fontweight="semibold", loc="left", pad=18)
        ax.text(
            0.0,
            1.01,
            subtitle,
            transform=ax.transAxes,
            fontsize=9.5,
            color="#666666",
            ha="left",
            va="bottom",
        )
    else:
        ax.set_title(title, fontsize=13, fontweight="semibold", loc="left", pad=10)


def _style_grid_and_spines(ax: Axes) -> None:
    ax.grid(visible=True, which="major", linestyle="-", linewidth=0.5, alpha=0.35)
    ax.grid(visible=True, which="minor", linestyle=":", linewidth=0.4, alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#888888")
    ax.spines["bottom"].set_color("#888888")
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)
