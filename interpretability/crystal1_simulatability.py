"""CRYSTAL-1 simulatability: can a K-leaf tree reproduce the DP champion's policy table?

WHY THIS EXISTS. CrystalScore for CRYSTAL-1 is Faithfulness x Simulatability x Stability. The
Faithfulness and Stability terms come from the E-21 transparency audit and ship as artifacts
(exp_e21_transparency_audit_report.json: naming monotone_frac 1.0, 10-seed belief corr 1.0,
mdl_deficit 0.0). The simulatability term was quoted in the papers as 0.92 -- "an 8-leaf tree
reproduces the goal-planner champion's policy table" -- but was never written to any artifact, so
the CRYSTAL-1 side of the comparison could not be reproduced from a clean clone. This computes it.

WHAT IT MEASURES. The DP champion's policy is a table: for every (years remaining, funding ratio
W/G) it names ONE book. That table IS the deployed policy, so "how simulatable is CRYSTAL-1" is
literally "how few rules does it take to restate that table". We fit a decision tree of at most K
leaves on the two named state coordinates and report its agreement with the table.

THE MANDATORY DUMB BASELINE. This project's register carries a rule bought by an earlier mistake:
a prediction bar passed by triviality because nobody compared against the dumbest possible model.
So every number below ships next to the majority-class baseline -- always answer the single most
common book -- and the honest quantity is the LIFT over it, not the raw accuracy. A table that is
90% one book is 90% "simulatable" by a constant, and that says nothing about legibility.

Run:  python interpretability/crystal1_simulatability.py
Out:  interpretability/crystal1_simulatability_report.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.tree import DecisionTreeClassifier, export_text

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "data" / "_personal_invest_registry" / "dp_policies"
OUT = Path(__file__).resolve().parent / "crystal1_simulatability_report.json"

LEAF_BUDGETS = (2, 4, 8, 16)
HEADLINE_K = 8  # the paper's "8-leaf tree"


def load_table(csv_path: Path) -> pd.DataFrame:
    """Wide (years_left x w_*) -> long (years_left, funding_ratio, book)."""
    wide = pd.read_csv(csv_path)
    w_cols = [c for c in wide.columns if c.startswith("w_")]
    long = wide.melt(id_vars=["years_left"], value_vars=w_cols,
                     var_name="w_col", value_name="book")
    long["funding_ratio"] = long["w_col"].str.slice(2).astype(float)
    return long[["years_left", "funding_ratio", "book"]]


def score_table(long: pd.DataFrame, seed: int = 0) -> dict:
    X = long[["years_left", "funding_ratio"]].to_numpy(float)
    y = long["book"].to_numpy()

    counts = pd.Series(y).value_counts()
    majority = float(counts.iloc[0] / len(y))

    per_k = {}
    for k in LEAF_BUDGETS:
        tree = DecisionTreeClassifier(max_leaf_nodes=k, random_state=seed).fit(X, y)
        fit_acc = float(tree.score(X, y))
        # Held-out check: the headline is a compression question (in-sample restatement of a
        # deterministic table), but a CV read tells us whether the rules generalise across the
        # grid or merely memorise cells.
        cv = KFold(n_splits=5, shuffle=True, random_state=seed)
        cv_acc = float(np.mean([
            DecisionTreeClassifier(max_leaf_nodes=k, random_state=seed)
            .fit(X[tr], y[tr]).score(X[te], y[te])
            for tr, te in cv.split(X)
        ]))
        per_k[str(k)] = {
            "leaves": int(tree.get_n_leaves()),
            "accuracy": round(fit_acc, 4),
            "cv_accuracy": round(cv_acc, 4),
            "lift_over_majority": round(fit_acc - majority, 4),
            # Chance-corrected, so a constant predictor scores 0 -- the ONLY form comparable to
            # R6c's simulatability, which is reported as 1 - SS_res/SS_tot and is already
            # baseline-adjusted. Raw accuracy and R-squared are not the same scale.
            "normalized": round((fit_acc - majority) / (1.0 - majority), 4) if majority < 1.0 else None,
        }

    head = DecisionTreeClassifier(max_leaf_nodes=HEADLINE_K, random_state=seed).fit(X, y)
    return {
        "n_cells": int(len(y)),
        "n_distinct_books": int(counts.size),
        "book_shares": {str(k): round(float(v) / len(y), 4) for k, v in counts.items()},
        "majority_class_baseline": round(majority, 4),
        "per_leaf_budget": per_k,
        "headline_k": HEADLINE_K,
        "simulatability_raw_accuracy": per_k[str(HEADLINE_K)]["accuracy"],
        "simulatability_lift": per_k[str(HEADLINE_K)]["lift_over_majority"],
        "simulatability_normalized": per_k[str(HEADLINE_K)]["normalized"],
        "rules": export_text(head, feature_names=["years_left", "funding_ratio"]).strip(),
    }


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    tables = sorted(POLICY_DIR.glob("dp_policy_*.csv"))
    if not tables:
        print(f"no policy tables under {POLICY_DIR}", file=sys.stderr)
        return 1

    cases = {}
    for csv_path in tables:
        name = csv_path.stem.replace("dp_policy_", "")
        cases[name] = score_table(load_table(csv_path))
        c = cases[name]
        print(f"{name:34s} cells={c['n_cells']:5d} books={c['n_distinct_books']} "
              f"| majority {c['majority_class_baseline']:.3f} "
              f"| 8-leaf {c['simulatability_raw_accuracy']:.3f} "
              f"| lift {c['simulatability_lift']:+.3f} "
              f"| normalized {c['simulatability_normalized']:.3f}")

    report = {
        "experiment": "CRYSTAL-1 simulatability - K-leaf tree vs the DP champion policy table",
        "why": ("the CrystalScore simulatability term for CRYSTAL-1 was quoted in the papers but "
                "never computed into an artifact; this makes it reproducible"),
        "method": {
            "features": ["years_left", "funding_ratio"],
            "label": "book chosen by the DP champion in that cell",
            "model": "DecisionTreeClassifier(max_leaf_nodes=K)",
            "leaf_budgets": list(LEAF_BUDGETS),
            "headline_k": HEADLINE_K,
        },
        "mandatory_dumb_baseline": ("majority class - always answer the most common book. Register "
                                    "rule: report the LIFT, never the raw accuracy alone."),
        "cases": cases,
        "artifacts": {"policy_tables": str(POLICY_DIR.relative_to(ROOT)).replace("\\", "/")},
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
