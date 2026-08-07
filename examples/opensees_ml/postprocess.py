"""Plot diagnostics from aggregate_and_train.py outputs.

Reads <indir>/<prefix>_preds.csv and produces a PDF/PNG with:
- feature histograms (NodalMass, LCol, E)
- target histogram (log period)
- predicted-vs-true scatter (train/test colored)
- residual histogram (or a "numerical-noise" annotation when residuals are at
  machine epsilon, e.g. exact physics recovery)
- coefficient bar chart with expected-physics reference lines
"""

import argparse
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

p = argparse.ArgumentParser()
p.add_argument("--indir", default="ml_results")
p.add_argument("--out-prefix", default="opensees_ml")
args = p.parse_args()

preds_path = os.path.join(args.indir, f"{args.out_prefix}_preds.csv")
model_path = os.path.join(args.indir, f"{args.out_prefix}_model.json")
pdf_path = os.path.join(args.indir, f"{args.out_prefix}_diagnostics.pdf")
png_path = os.path.join(args.indir, f"{args.out_prefix}_diagnostics.png")

df = pd.read_csv(preds_path)
with open(model_path) as f:
    model = json.load(f)

train = df[df["split"] == "train"]
test = df[df["split"] == "test"]

fig, axes = plt.subplots(2, 4, figsize=(16, 8))
COL_TRAIN = "#1f77b4"
COL_TEST = "#d62728"

# Row 1: feature histograms + target
for ax, col, color, label in [
    (axes[0, 0], "NodalMass", "#4c72b0", "NodalMass (kip·s²/in)"),
    (axes[0, 1], "LCol", "#55a868", "LCol (in)"),
    (axes[0, 2], "E", "#c44e52", "E (ksi)"),
]:
    ax.hist(df[col], bins=12, color=color, edgecolor="white")
    ax.set_xlabel(label)
    ax.set_ylabel("count")
    ax.set_title(f"Feature: {col}")

ax = axes[0, 3]
ax.hist(df["log_target"], bins=20, color="#8172b2", edgecolor="white")
ax.set_xlabel("log(period)")
ax.set_ylabel("count")
ax.set_title(f"Target: log(period)  (n={len(df)})")

# Row 2: predicted vs true, residuals, residual-vs-predicted, coefficients
ax = axes[1, 0]
ax.scatter(
    train["log_target"],
    train["log_pred"],
    s=18,
    c=COL_TRAIN,
    alpha=0.7,
    label=f"train (n={len(train)})",
)
ax.scatter(
    test["log_target"],
    test["log_pred"],
    s=28,
    c=COL_TEST,
    alpha=0.9,
    label=f"test (n={len(test)})",
    marker="^",
)
lo = df[["log_target", "log_pred"]].min().min()
hi = df[["log_target", "log_pred"]].max().max()
ax.plot([lo, hi], [lo, hi], "k--", lw=1, label="y = x")
ax.set_xlabel("log(period) — truth")
ax.set_ylabel("log(period) — predicted")
ax.set_title(
    f"Predicted vs. truth\n"
    f"R² train={model['r2_train']:.4f}  test={model['r2_test']:.4f}"
)
ax.legend(loc="upper left", fontsize=8)

# Residual histogram with machine-epsilon fallback
ax = axes[1, 1]
resid = df["resid"].values
finite = resid[np.isfinite(resid)]
resid_scale = float(np.max(np.abs(finite))) if finite.size else 0.0

if resid_scale < 1.0e-6:
    ax.text(
        0.5,
        0.5,
        "Residuals at machine epsilon\n"
        f"max|resid| = {resid_scale:.2e}\n"
        "(model recovers physics exactly)",
        ha="center",
        va="center",
        transform=ax.transAxes,
        fontsize=11,
        color="#444",
    )
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Residuals")
else:
    ax.hist(finite, bins=20, color="#937860", edgecolor="white")
    ax.axvline(0, color="k", ls="--", lw=1)
    ax.set_xlabel("residual = log(period) − pred")
    ax.set_ylabel("count")
    ax.set_title(f"Residuals  (std = {finite.std():.3e})")

# Residual vs predicted (diagnostic for bias/heteroscedasticity)
ax = axes[1, 2]
if resid_scale < 1.0e-6:
    ax.text(
        0.5,
        0.5,
        "Residual scatter omitted\n(see panel at left)",
        ha="center",
        va="center",
        transform=ax.transAxes,
        fontsize=10,
        color="#666",
    )
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Residual vs. predicted")
else:
    ax.scatter(
        train["log_pred"], train["resid"], s=18, c=COL_TRAIN, alpha=0.7, label="train"
    )
    ax.scatter(
        test["log_pred"],
        test["resid"],
        s=28,
        c=COL_TEST,
        alpha=0.9,
        label="test",
        marker="^",
    )
    ax.axhline(0, color="k", ls="--", lw=1)
    ax.set_xlabel("log(period) — predicted")
    ax.set_ylabel("residual")
    ax.set_title("Residual vs. predicted")
    ax.legend(loc="upper right", fontsize=8)

# Coefficient bar chart vs. physics expectation
ax = axes[1, 3]
names = model["feature_names"]
coef = model["coef"]
# Expected from T = 2π sqrt(M L^3 / (3 E I)):
expected_map = {
    "bias": None,  # depends on Iz, not annotated
    "log_NodalMass": 0.5,
    "log_LCol": 1.5,
    "log_E": -0.5,
}
x = np.arange(len(names))
bars = ax.bar(x, coef, color="#4c72b0", edgecolor="white")
for xi, name in zip(x, names):
    exp = expected_map.get(name)
    if exp is not None:
        ax.plot(
            [xi - 0.4, xi + 0.4],
            [exp, exp],
            color="#d62728",
            lw=2,
            label=("physics expectation" if xi == 1 else None),
        )
ax.axhline(0, color="k", lw=0.8)
ax.set_xticks(x)
ax.set_xticklabels(names, rotation=20, ha="right", fontsize=8)
ax.set_ylabel("coefficient")
ax.set_title("Fitted coefficients")
ax.legend(fontsize=8, loc="best")

fig.suptitle("OpenSees ML — diagnostic plots", fontsize=14, y=1.00)
fig.tight_layout()
fig.savefig(pdf_path)
fig.savefig(png_path, dpi=110)
print(f"Wrote {pdf_path}")
print(f"Wrote {png_path}")
