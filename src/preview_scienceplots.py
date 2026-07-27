"""Render the full figure set in SciencePlots 'science' (serif) style into a
separate preview folder — does NOT touch paper/figures/. For the authors to
compare against the current modern-sans figures before deciding to adopt."""
from pathlib import Path
import matplotlib.pyplot as plt
import scienceplots  # noqa: F401  (registers styles)

import vizstyle as V

PREV = Path(__file__).resolve().parent.parent / "social" / "preview_v2"
PREV.mkdir(parents=True, exist_ok=True)
V.FIG = PREV  # redirect V.save() output

_base = V.apply
def science_apply():
    plt.style.use(["science", "no-latex", "grid"])   # serif journal base
    plt.rcParams.update({
        "figure.dpi": 150, "savefig.dpi": 300,
        "figure.facecolor": "white", "savefig.facecolor": "white",
        "axes.facecolor": "white", "savefig.bbox": "tight",
        "legend.frameon": False, "axes.titlelocation": "center",
    })
V.apply = science_apply

# import AFTER patching so their module-level V.apply() picks it up
import figures            # noqa: E402
import figures_betting    # noqa: E402
figures.main()
figures_betting.main()
print(f"\npreview figures written to {PREV}")
