"""Sensitivity sweep + multi-seed calibration for the information-gain ranker feature.

This is an *evidence-gathering* harness, not a validation suite. The bundled
``examples/demo_notes`` corpus has only a handful of eligible links, so the
numbers here are coarse by construction. The point is to answer three questions
honestly on whatever corpus you point it at:

1. On/Off (leave-one-out): does turning the information-gain feature on change
   link-reconstruction at all, versus turning it off (weight = 0)?
2. Sensitivity (leave-one-out grid): over the three feature hyperparameters
   (``information_gain`` weight, ``entropy_temperature``, ``information_gain_boost``),
   where does the feature help, stay inert, or regress?
3. Multi-seed random-holdout: what does the seed-to-seed distribution look like,
   so a single-seed eval number is not mistaken for a stable measurement?

Leave-one-out (LOO) is used as the primary signal because, on a small corpus,
hiding one eligible edge at a time and ranking its target uses all the data and
removes the random-sampling noise that a single ``--seed`` introduces.

Usage:
    python scripts/sweep_information_gain.py --src examples/demo_notes
    python scripts/sweep_information_gain.py --src /path/to/vault --json out.json
"""

from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import replace
from pathlib import Path

from orphan_radar.core.settings import RadarSettings
from orphan_radar.eval.link_reconstruction import (
    calibrate_weights,
    evaluate_weights,
    make_eval_summary,
    select_eligible_edges,
)
from orphan_radar.graph.build_graph import build_link_graph
from orphan_radar.ingest.loader import load_notes

# Feature hyperparameters under test. The feature only contributes to the score
# when BOTH the weight and the boost are > 0 (see rank/information_gain.py).
WEIGHT_GRID = (0.0, 0.04, 0.08, 0.16, 0.32, 0.64)
TEMPERATURE_GRID = (0.1, 0.25, 0.5, 1.0)
BOOST_GRID = (0.0, 0.35, 1.0)


def _loo_eval(notes, eligible, settings: RadarSettings) -> dict:
    """Leave-one-out reconstruction over every eligible edge.

    Returns aggregate recall@{1,3,5} and MRR across all scorable held-out edges.
    """
    r1 = r3 = r5 = 0
    rr_sum = 0.0
    scored = 0
    for edge in eligible:
        res = evaluate_weights(notes, [edge], settings, eligible_count=len(eligible))
        if res.scored_edges == 0:
            continue
        scored += 1
        # With a single hidden edge each recall_at_k is 0/1 and mrr == 1/rank.
        r1 += int(res.recall_at_1 >= 1.0)
        r3 += int(res.recall_at_3 >= 1.0)
        r5 += int(res.recall_at_5 >= 1.0)
        rr_sum += res.mean_reciprocal_rank
    if scored == 0:
        return {"scored": 0, "recall_at_1": 0.0, "recall_at_3": 0.0,
                "recall_at_5": 0.0, "mrr": 0.0}
    return {
        "scored": scored,
        "recall_at_1": round(r1 / scored, 4),
        "recall_at_3": round(r3 / scored, 4),
        "recall_at_5": round(r5 / scored, 4),
        "mrr": round(rr_sum / scored, 4),
    }


def _feature_off(settings: RadarSettings) -> RadarSettings:
    # Inert config: zero weight AND zero boost so the feature contributes nothing.
    return replace(settings, information_gain=0.0, information_gain_boost=0.0)


def run(src: Path) -> dict:
    base = RadarSettings()
    notes, _ = load_notes(src, base)
    graph = build_link_graph(list(notes))
    eligible = select_eligible_edges(graph)

    report: dict = {
        "corpus": str(src),
        "notes": len(notes),
        "eligible_edges": len(eligible),
        "default_weights": {
            "information_gain": base.information_gain,
            "entropy_temperature": base.entropy_temperature,
            "information_gain_boost": base.information_gain_boost,
        },
    }
    if len(eligible) < 3:
        report["status"] = "too_small"
        report["note"] = "Fewer than 3 eligible edges; reconstruction eval is not meaningful."
        return report

    # 1. On/Off via leave-one-out.
    off = _loo_eval(notes, eligible, _feature_off(base))
    on = _loo_eval(notes, eligible, base)  # defaults: weight 0.08, temp 0.25, boost 0.35
    report["loo_on_off"] = {
        "off": off,
        "on_default": on,
        "delta_recall_at_5": round(on["recall_at_5"] - off["recall_at_5"], 4),
        "delta_mrr": round(on["mrr"] - off["mrr"], 4),
        "identical": off == on,
    }

    # 2. Sensitivity grid (leave-one-out). Records every combo + whether it
    #    regresses below the feature-off baseline on recall@5.
    grid: list[dict] = []
    off_r5 = off["recall_at_5"]
    off_mrr = off["mrr"]
    for w in WEIGHT_GRID:
        for t in TEMPERATURE_GRID:
            for b in BOOST_GRID:
                s = replace(base, information_gain=w, entropy_temperature=t,
                            information_gain_boost=b)
                res = _loo_eval(notes, eligible, s)
                inert = (w == 0.0 or b == 0.0)
                grid.append({
                    "information_gain": w,
                    "entropy_temperature": t,
                    "information_gain_boost": b,
                    "inert_config": inert,
                    "recall_at_5": res["recall_at_5"],
                    "mrr": res["mrr"],
                    "regresses_vs_off": res["recall_at_5"] < off_r5 - 1e-9,
                })
    report["sensitivity_grid"] = grid
    active = [g for g in grid if not g["inert_config"]]
    report["sensitivity_summary"] = {
        "grid_points": len(grid),
        "active_points": len(active),
        "recall_at_5_min": min(g["recall_at_5"] for g in grid),
        "recall_at_5_max": max(g["recall_at_5"] for g in grid),
        "mrr_min": min(g["mrr"] for g in grid),
        "mrr_max": max(g["mrr"] for g in grid),
        "active_points_regressing": sum(1 for g in active if g["regresses_vs_off"]),
        "active_points_improving_r5": sum(1 for g in active if g["recall_at_5"] > off_r5 + 1e-9),
        "off_baseline_recall_at_5": off_r5,
        "off_baseline_mrr": off_mrr,
    }

    # 3. Multi-seed random-holdout (characterizes the single-seed noise directly).
    seeds = list(range(30))
    ratio = 0.30
    on_r5, on_mrr, off_r5_s, off_mrr_s = [], [], [], []
    off_settings = _feature_off(base)
    for seed in seeds:
        e_on = make_eval_summary(notes, base, holdout_ratio=ratio, seed=seed)
        e_off = make_eval_summary(notes, off_settings, holdout_ratio=ratio, seed=seed)
        on_r5.append(e_on.recall_at_5)
        on_mrr.append(e_on.mean_reciprocal_rank)
        off_r5_s.append(e_off.recall_at_5)
        off_mrr_s.append(e_off.mean_reciprocal_rank)

    def _stats(xs):
        return {
            "mean": round(statistics.mean(xs), 4),
            "stdev": round(statistics.pstdev(xs), 4),
            "min": round(min(xs), 4),
            "max": round(max(xs), 4),
        }

    diffs_r5 = [a - b for a, b in zip(on_r5, off_r5_s)]
    report["multiseed"] = {
        "seeds": len(seeds),
        "holdout_ratio": ratio,
        "on_recall_at_5": _stats(on_r5),
        "off_recall_at_5": _stats(off_r5_s),
        "on_mrr": _stats(on_mrr),
        "off_mrr": _stats(off_mrr_s),
        "seeds_on_beats_off_r5": sum(1 for d in diffs_r5 if d > 1e-9),
        "seeds_off_beats_on_r5": sum(1 for d in diffs_r5 if d < -1e-9),
        "seeds_tied_r5": sum(1 for d in diffs_r5 if abs(d) <= 1e-9),
    }

    # 4. Multi-seed calibration stability (the full random-search over all weights).
    cal = []
    for seed in range(10):
        c = calibrate_weights(notes, base, holdout_ratio=ratio, trials=40, seed=seed)
        cal.append({
            "seed": seed,
            "improved": c.improved,
            "baseline_r5": c.baseline.recall_at_5,
            "best_r5": c.best.recall_at_5,
            "best_information_gain_weight": c.best_weights.get("information_gain"),
        })
    report["calibration_stability"] = {
        "runs": len(cal),
        "runs_claiming_improvement": sum(1 for c in cal if c["improved"]),
        "best_information_gain_weight_values": sorted(
            {round(c["best_information_gain_weight"], 3) for c in cal}
        ),
        "detail": cal,
    }
    report["status"] = "ok"
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", type=Path, default=Path("examples/demo_notes"),
                    help="Notes directory to sweep.")
    ap.add_argument("--json", type=Path, default=None,
                    help="Optional path to write the full report as JSON.")
    args = ap.parse_args()

    report = run(args.src)
    print(json.dumps(report, indent=2))
    if args.json:
        args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
