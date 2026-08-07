"""Aggregate per-task metrics.json files and fit a linear regression.

Target:   log(period)
Features: log(NodalMass), log(LCol), log(E)   + intercept

Recovers the physics T = 2*pi*sqrt(M*L^3 / (3*E*I)) => coefficients
approximately [const, 0.5, 1.5, -0.5] with R^2 == 1.0.
"""

import argparse
import glob
import json
import os
import sys

import numpy as np

p = argparse.ArgumentParser()
p.add_argument("--indir", default=".", help="Root containing out_*/metrics.json")
p.add_argument("--outdir", default="ml_results")
p.add_argument("--out-prefix", default="opensees_ml")
p.add_argument("--target", default="period", choices=["period", "top_disp_at_100kip"])
p.add_argument("--test-frac", type=float, default=0.20)
p.add_argument("--seed", type=int, default=12345)
args = p.parse_args()

os.makedirs(args.outdir, exist_ok=True)

# 1) Collect per-task metrics
pattern = os.path.join(args.indir, "out_*", "metrics.json")
files = sorted(glob.glob(pattern))
if not files:
    print(f"ERROR: no files matched {pattern}", file=sys.stderr)
    sys.exit(1)

rows = []
for fp in files:
    with open(fp) as fh:
        rows.append(json.load(fh))
print(f"Aggregated {len(rows)} task results.")

# 2) Feature matrix in log space
feature_keys = ["NodalMass", "LCol", "E"]
X_raw = np.array([[r[k] for k in feature_keys] for r in rows], dtype=float)
y_raw = np.array([r[args.target] for r in rows], dtype=float)

X_log = np.log(X_raw)
y_log = np.log(y_raw)
X = np.column_stack([np.ones(X_log.shape[0]), X_log])
feat_names = ["bias"] + [f"log_{k}" for k in feature_keys]

# 3) Train/test split
rng = np.random.default_rng(args.seed)
n = X.shape[0]
idx = np.arange(n)
rng.shuffle(idx)
n_test = max(1, int(round(args.test_frac * n)))
test_mask = np.zeros(n, dtype=bool)
test_mask[idx[:n_test]] = True
train_mask = ~test_mask

# 4) Fit (sklearn preferred, lstsq fallback)
try:
    from sklearn.linear_model import LinearRegression

    model = LinearRegression(fit_intercept=False)
    model.fit(X[train_mask], y_log[train_mask])
    coef = np.asarray(model.coef_, dtype=float)
    fitter = "sklearn"
except Exception:
    coef, *_ = np.linalg.lstsq(X[train_mask], y_log[train_mask], rcond=None)
    fitter = "lstsq"


def r2(y_true, y_pred):
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")


yhat_log = X @ coef
r2_train = r2(y_log[train_mask], yhat_log[train_mask])
r2_test = r2(y_log[test_mask], yhat_log[test_mask])

# 5) Per-task predictions CSV
preds_path = os.path.join(args.outdir, f"{args.out_prefix}_preds.csv")
with open(preds_path, "w") as f:
    cols = feature_keys + ["target_raw", "log_target", "log_pred", "resid", "split"]
    f.write(",".join(cols) + "\n")
    for i in range(n):
        split = "test" if test_mask[i] else "train"
        vals = [f"{X_raw[i, j]:.6g}" for j in range(len(feature_keys))] + [
            f"{y_raw[i]:.6g}",
            f"{y_log[i]:.6g}",
            f"{yhat_log[i]:.6g}",
            f"{y_log[i] - yhat_log[i]:.6g}",
            split,
        ]
        f.write(",".join(vals) + "\n")

# 6) Model JSON
model_path = os.path.join(args.outdir, f"{args.out_prefix}_model.json")
with open(model_path, "w") as f:
    json.dump(
        {
            "type": "linear_regression",
            "fitter": fitter,
            "target": args.target,
            "target_space": "log",
            "feature_names": feat_names,
            "coef": coef.tolist(),
            "r2_train": r2_train,
            "r2_test": r2_test,
            "n_train": int(np.sum(train_mask)),
            "n_test": int(np.sum(test_mask)),
            "seed": args.seed,
        },
        f,
        indent=2,
    )

# 7) Report
report_path = os.path.join(args.outdir, f"{args.out_prefix}_report.txt")
with open(report_path, "w") as f:
    f.write(f"n_total:  {n}\n")
    f.write(f"n_train:  {int(np.sum(train_mask))}\n")
    f.write(f"n_test:   {int(np.sum(test_mask))}\n")
    f.write(f"target:   {args.target} (log space)\n")
    f.write(f"R2 train: {r2_train:.4f}\n")
    f.write(f"R2 test:  {r2_test:.4f}\n")
    f.write(f"fitter:   {fitter}\n\n")
    for name, c in zip(feat_names, coef.tolist()):
        f.write(f"coef_{name}: {c:.6f}\n")

print(f"Wrote {preds_path}")
print(f"Wrote {model_path}")
print(f"Wrote {report_path}")
print(f"R^2 train={r2_train:.4f}, test={r2_test:.4f}")
