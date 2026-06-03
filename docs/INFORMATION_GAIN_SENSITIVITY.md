# Information-Gain Sensitivity & Calibration Study

Status: evidence note. This documents an **empirical sensitivity sweep** of the
Shannon information-gain ranker feature (red-team follow-ups **F7** sensitivity
and **F8** multi-seed). It is **evidence-gathering, not validation**: the only
corpus available here is the bundled `examples/demo_notes`, which has just
**7 eligible links**. Numbers on a corpus this small are coarse by construction.
Read the conclusions as "what the feature does on a tiny graph," not as proof of
value on a real vault.

Reproduce with:

```bash
python scripts/sweep_information_gain.py --src examples/demo_notes --json sweep.json
# or point at a larger vault:
python scripts/sweep_information_gain.py --src /path/to/vault
```

## What was measured

The feature contributes to ranking only through the additive term
`settings.information_gain * information.information_gain`, and that term is
non-zero only when **both** the `information_gain` weight and the
`information_gain_boost` are `> 0` and the orphan routes to `>= 2` communities
(see `rank/information_gain.py`). So the sweep varies the three feature
hyperparameters and compares against a fully-inert "feature off" config
(`information_gain = 0`, `information_gain_boost = 0`).

Primary metric is **leave-one-out (LOO)** link reconstruction: hide each of the
7 eligible edges one at a time, rank its target, aggregate recall@{1,3,5} and
MRR. LOO uses all the data and removes the random-sampling noise that a single
`--seed` introduces. A 30-seed random-holdout run characterizes that noise
directly.

## Results on `examples/demo_notes` (8 notes, 7 eligible edges)

### 1. On vs. off at default settings — the feature is inert here

| Config | recall@1 | recall@3 | recall@5 | MRR |
|---|---|---|---|---|
| Feature **off** (`weight=0, boost=0`) | 0.714 | 0.857 | 0.857 | 0.786 |
| Feature **on** (defaults: `weight=0.08, temp=0.25, boost=0.35`) | 0.714 | 0.857 | 0.857 | 0.786 |
| **Delta** | 0 | 0 | 0 | 0 |

At the shipped defaults the feature changes **nothing** on this corpus: every
held-out target ranks identically with and without it. This confirms red-team
finding **A1** (no empirical lift on a small corpus) and confirms the feature is
**non-regressive** at defaults.

### 2. Sensitivity grid (72 points: weight × temperature × boost)

- **recall@5 is invariant at 0.857 across the entire grid** (min = max). No
  hyperparameter combination improves recall, and none regresses it.
- **MRR is the only thing that moves, and only downward.** Across the 40
  active (non-inert) configs:
  - 30 configs leave MRR at the off-baseline `0.786` (no effect),
  - 6 configs drop MRR to `0.714`,
  - 4 configs drop MRR to `0.643`.
- The MRR drops appear only at **aggressive** settings — `information_gain`
  weight `>= 0.16` combined with `information_gain_boost = 1.0` (and the most
  aggressive `weight = 0.32–0.64`). There the feature reorders within the
  top-5 and slightly *worsens* the average rank of the correct target.
- **No active config improved recall@5; no active config improved MRR.**

Read plainly: on this corpus the feature's best case is "harmless," and its
worst case is "mildly harmful if over-weighted."

### 3. Multi-seed random-holdout (30 seeds, holdout ratio 0.30)

| Metric | On (mean ± sd) | Off (mean ± sd) | min–max |
|---|---|---|---|
| recall@5 | 0.933 ± 0.170 | 0.933 ± 0.170 | 0.5 – 1.0 |
| MRR | 0.701 ± 0.265 | 0.701 ± 0.265 | 0.225 – 1.0 |

On and off are **identical on all 30 seeds** (0 seeds where on beats off, 0
where off beats on, 30 tied). The large standard deviations (±0.17 recall@5,
±0.26 MRR) quantify exactly why a single-seed eval number is unreliable here:
the seed picks 2 of 7 edges, so the metric swings widely by chance.

### 4. Calibration stability — calibration on this corpus is noise

Running the full 9-weight random-search calibrator (`--calibrate`, 40 trials)
across 10 seeds:

- recall@5 is `1.0` for both baseline and "best" in **every** run — the
  reported `improved: true` (7/10 runs) is only the **MRR tiebreaker** moving,
  not a recall gain.
- The "best" `information_gain` weight the search lands on scatters across
  `{0.007, 0.017, 0.057, 0.08, 0.12, 0.169, 0.191, 0.384}` — roughly a **50×
  spread** with no recall improvement to justify any of them.

The calibrated weight is essentially random on 7 edges. **Do not adopt a
calibrated weight vector from a corpus this small.**

## Conclusions and safe ranges

1. **Keep the default weight low.** `information_gain = 0.08`,
   `entropy_temperature = 0.25`, `information_gain_boost = 0.35` keep the
   feature neutral (no regression) on this corpus. This is the recommended
   safe range.
2. **Avoid over-weighting.** `information_gain >= 0.16` together with
   `information_gain_boost = 1.0` is the only region that *changed* anything,
   and the change was a small MRR *degradation*. Treat that region as unsafe
   absent contrary evidence from a larger corpus.
3. **Do not tune weights against this corpus.** Calibration here is
   indistinguishable from noise (point 4 above). The random-search calibrator
   should only be trusted on a vault with many more eligible edges.
4. **The feature is safe to keep on (red-team F14).** It is non-regressive on
   recall@{1,3,5} at sane settings, fully guarded (NaN/Inf, clamp-to-zero), and
   defaulted low. Its plausible upside is on larger, more genuinely
   graph-structured corpora where community routing is actually ambiguous —
   which this 8-note demo is not.

## Honest limitations

- 7 eligible edges is far too few to detect a small real effect; absence of
  lift here is **not** evidence of absence of lift on a real vault.
- The demo corpus has very few communities, so routing entropy (the quantity
  the feature reduces) is small to begin with — the feature has little to act
  on by construction.
- The right next step is to re-run `scripts/sweep_information_gain.py` against a
  real multi-hundred-note vault before drawing any conclusion stronger than
  "non-regressive at defaults."
