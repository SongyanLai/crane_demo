import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
plt.rcParams.update({"font.size": 9, "font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
rows = [r for r in json.load(open("analysis/all_runs.json")) if r["main"]]
models = ["ChatGPT", "DeepSeek", "Claude", "Gemini"]
cells = [("orig-B", "Original text\nno tool (B)"), ("orig-C", "Original text\nwith Kind 2 (C)"), ("ground-B", "Original text +\ndomain notes (B)"), ("shall-B", "#4 written\nas 'shall' (B)")]
BLUE, ORANGE, GREEN, RED, GREY, PURPLE = "#0072B2", "#E69F00", "#009E73", "#D55E00", "#999999", "#CC79A7"
OUT = "report/figures/"
import os; os.makedirs(OUT, exist_ok=True)

# Figure 2: reading of #4 in the first translation
fig, ax = plt.subplots(figsize=(7.2, 2.6))
x, xt, xl = 0, [], []
for ci, (c, lab) in enumerate(cells):
    for m in models:
        sub = [r for r in rows if r["cell"] == c and r["model"] == m]
        p = sum(r["read4"] == "permission" for r in sub); o = len(sub) - p
        ax.bar(x, p, color=GREY, width=0.8); ax.bar(x, o, bottom=p, color=BLUE, width=0.8)
        xt.append(x); xl.append(m); x += 1
    x += 0.8
ax.set_xticks(xt); ax.set_xticklabels(xl, rotation=90, fontsize=7.5)
for ci, (c, lab) in enumerate(cells):
    ax.text(ci * 4.8 + 1.5, 3.25, lab, ha="center", va="bottom", fontsize=8)
ax.set_ylim(0, 4.3); ax.set_yticks([0, 1, 2, 3]); ax.set_ylabel("runs (of 3)")
ax.legend(handles=[Patch(color=GREY, label="#4 read as a permission (no lowering rule)"), Patch(color=BLUE, label="#4 read as an obligation (lowering required)")],
          loc="upper center", bbox_to_anchor=(0.5, -0.42), ncol=2, frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(OUT + "fig_reading4.pdf"); plt.close(fig)

# Figure 3: main outcomes per cell
metrics = [("claim_correct", "Verdict matches Kind 2", GREY), ("both_conflicts", "Both conflicts named", BLUE),
           ("good_final", "Good final contract", GREEN)]
fig, ax = plt.subplots(figsize=(7.2, 2.6))
w = 0.26
for i, (k, lab, col) in enumerate(metrics):
    vals = [100 * sum(1 for r in rows if r["cell"] == c and r[k] is True) / 12 for c, _ in cells]
    bars = ax.bar([j + (i - 1) * w for j in range(4)], vals, width=w, color=col, label=lab)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + w / 2, v + 1.5, f"{round(v * 12 / 100)}/12", ha="center", fontsize=7)
ax.set_xticks(range(4)); ax.set_xticklabels([l for _, l in cells], fontsize=8)
ax.set_ylim(0, 115); ax.set_ylabel("% of runs"); ax.legend(ncol=3, frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, 1.18))
fig.tight_layout(); fig.savefig(OUT + "fig_outcomes.pdf"); plt.close(fig)

# Figure 4: good final contract per model and cell (heat map)
import numpy as np
M = np.array([[sum(1 for r in rows if r["cell"] == c and r["model"] == m and r["good_final"]) for c, _ in cells] for m in models])
fig, ax = plt.subplots(figsize=(5.6, 2.5))
ax.imshow(M, cmap="Greens", vmin=0, vmax=3.6)
for i in range(4):
    for j in range(4):
        ax.text(j, i, f"{M[i, j]}/3", ha="center", va="center", fontsize=9, color="black")
ax.set_xticks(range(4)); ax.set_xticklabels(["Original,\nno tool (B)", "Original,\nKind 2 (C)", "Domain\nnotes (B)", "'shall'\ntext (B)"], fontsize=8)
ax.set_yticks(range(4)); ax.set_yticklabels(models)
for s in ax.spines.values(): s.set_visible(False)
ax.tick_params(length=0)
fig.tight_layout(); fig.savefig(OUT + "fig_goodfinal.pdf"); plt.close(fig)

# Figure 5: arm C tool use
crows = sorted([r for r in rows if r["arm"] == "C"], key=lambda r: (models.index(r["model"]), r["run_id"]))
fig, ax = plt.subplots(figsize=(7.0, 3.1))
col = {"realizable": GREEN, "unrealizable": RED, "syntax error": GREY}
for i, r in enumerate(crows):
    seq = r["run_verdicts"].split(" > ")
    for j, v in enumerate(seq):
        ax.scatter(j + 1, i, s=90, color=col[v], edgecolor="black", linewidth=0.4, zorder=3)
    ax.plot([1, len(seq)], [i, i], color="#cccccc", zorder=1)
    fx = 5.8
    lab = {"tested": "final contract = last tested one", "equivalent to tested": "final contract = run 1 (same rules)",
           "not run": "final contract not run by the model"}[r["final_status"]]
    ax.text(fx, i, lab + ("; good" if r["good_final"] else "; not good"), va="center", fontsize=7)
ax.set_yticks(range(len(crows))); ax.set_yticklabels([f'{r["run_id"]} {r["model"]}' for r in crows], fontsize=7.5)
ax.set_xticks(range(1, 6)); ax.set_xlabel("Kind 2 run requested by the model"); ax.set_xlim(0.5, 10.4); ax.invert_yaxis()
ax.legend(handles=[Patch(color=GREEN, label="realizable"), Patch(color=RED, label="unrealizable"), Patch(color=GREY, label="syntax error")],
          loc="upper center", bbox_to_anchor=(0.3, -0.2), ncol=3, fontsize=7.5, frameon=False)
fig.tight_layout(); fig.savefig(OUT + "fig_tooluse.pdf"); plt.close(fig)
print("figures written")
