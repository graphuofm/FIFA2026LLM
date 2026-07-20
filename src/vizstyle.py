"""One shared visual system for every figure (consistency is the point).

Rule that removes the earlier colour clashes:
  * MODEL IDENTITY  -> four fixed hues that are NOT green and NOT red
                       (blue / violet / pink / amber). Used only for a model.
  * MARKET          -> neutral slate grey (a reference, not a competitor).
  * STATUS/OUTCOME  -> green = good/correct/profit, red = bad/wrong/loss,
                       grey = neutral/partial. Never a model.
  * MAGNITUDE       -> one blue sequential ramp for heat.
So green never means "ChatGPT" and amber never means "penalty": a colour has one
job across the whole paper. Per-model marker shapes give a second, CVD- and
greyscale-safe channel.
"""
from __future__ import annotations
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt

FIG = Path(__file__).resolve().parent.parent / "paper" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

MODELS = ["claude", "chatgpt", "gemini", "grok"]
MODEL_COLOR = {
    "claude":  "#1c6fd0",   # blue
    "chatgpt": "#6b40d8",   # violet
    "gemini":  "#e64980",   # pink
    "grok":    "#e8830c",   # amber
}
MODEL_MARKER = {"claude": "o", "chatgpt": "s", "gemini": "^", "grok": "D"}
MODEL_LABEL = {"claude": "Claude", "chatgpt": "ChatGPT",
               "gemini": "Gemini", "grok": "Grok"}
MARKET_COLOR = "#3f4752"          # slate grey — the market baseline

# status / outcome (reserved; never a model hue)
GOOD, BAD, MID = "#2f9e44", "#e03131", "#aeb4bb"
SEQ = "Blues"                     # single magnitude ramp for heatmaps

# ink / chrome
INK, INK2, MUTED = "#15181c", "#5b636b", "#9aa0a6"
GRID, BASE = "#eceef0", "#c7ccd1"
SURFACE = "#ffffff"

COL1, COL2 = 3.35, 7.0            # ACM column / full width (inches)


def apply():
    mpl.rcParams.update({
        "figure.dpi": 150, "savefig.dpi": 300,
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 8.6, "axes.titlesize": 9.6, "axes.labelsize": 8.6,
        "xtick.labelsize": 8.0, "ytick.labelsize": 8.0, "legend.fontsize": 8.0,
        "axes.edgecolor": BASE, "axes.linewidth": 0.8,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7,
        "axes.axisbelow": True, "axes.facecolor": SURFACE,
        "figure.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.labelcolor": INK, "text.color": INK,
        "xtick.major.size": 0, "ytick.major.size": 0,
        "legend.frameon": False, "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
        "axes.titlelocation": "left", "axes.titlepad": 8.0,
    })


def despine(ax, left=True, bottom=True):
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_visible(left)
    ax.spines["bottom"].set_visible(bottom)
    ax.spines["left"].set_color(BASE)
    ax.spines["bottom"].set_color(BASE)


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf")
    fig.savefig(FIG / f"{name}.png", dpi=200)
    plt.close(fig)
    print(f"  wrote figures/{name}.pdf + .png")
