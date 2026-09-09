normaliser: `basic`  prefixes: first 1.0 s, step 0.5 s  aligner: `qwen3-forced-aligner-0.6b`

**Settle metrics** (95% bootstrap CI over utterances; lags quantised by the step, read differences not absolutes)

| model | condition | n | median lag | p90 lag | lag defined | revisions /100 (pooled) | revisions /100 (median utt) | unstable tail | agree before end | stream RTF | ×audio | empty partials | exploded partials | max partial words |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| parakeet-tdt-0.6b-v3 | clean | 2620 | 100 ms [100, 100] | 600 ms [540, 620] | 98% | 51.4 [46.7, 56.5] | 33.3 [33.3, 35.7] | 0.50 [0.44, 0.57] | 0.38 s [0.37, 0.39] | 0.062 | 11.7 | 919 | 41 | 509 |
| parakeet-tdt-0.6b-v3 | pots_babble10 | 2620 | 200 ms [180, 200] | 1200 ms [1120, 1280] | 95% | 93.9 [83.3, 106.2] | 36.7 [35.0, 38.5] | 1.07 [0.92, 1.25] | 0.32 s [0.31, 0.33] | 0.063 | 11.7 | 1950 | 104 | 1019 |

**Change vs clean, same utterances, paired 95% CI** (an interval that excludes 0 means the condition really changed how the model settles)

| model | condition | Δ median lag | Δ p90 lag | Δ revisions /100 (pooled) | Δ revisions /100 (median utt) | Δ unstable tail | Δ agree before end |
|---|---|---:|---:|---:|---:|---:|---:|
| parakeet-tdt-0.6b-v3 | pots_babble10 | +100 [+80, +100] ms | +600 [+540, +700] ms | +42.5 [+30.6, +54.7] | +3.3 [+0.4, +5.1] | +0.57 [+0.40, +0.75] | -0.05 [-0.07, -0.04] s |
