normaliser: `whisper_en`  prefixes: first 1.0 s, step 0.5 s  aligner: `qwen3-forced-aligner-0.6b`

**Settle metrics** (95% bootstrap CI over utterances; lags quantised by the step, read differences not absolutes)

| model | condition | n | median lag | p90 lag | lag defined | revisions /100 (pooled) | revisions /100 (median utt) | unstable tail | agree before end | stream RTF | ×audio | empty partials | exploded partials | max partial words |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| parakeet-tdt-0.6b-v3 | clean | 2620 | 100 ms [100, 100] | 580 ms [520, 600] | 98% | 49.3 [44.8, 54.3] | 33.3 [31.6, 33.3] | 0.50 [0.44, 0.56] | 0.40 s [0.38, 0.41] | 0.062 | 11.7 | 927 | 41 | 509 |
| parakeet-tdt-0.6b-v3 | pots_babble10 | 2620 | 200 ms [180, 200] | 1200 ms [1120, 1280] | 96% | 92.9 [82.3, 104.9] | 36.0 [33.3, 37.5] | 1.07 [0.92, 1.25] | 0.33 s [0.32, 0.34] | 0.063 | 11.7 | 1969 | 104 | 1019 |

**Change vs clean, same utterances, paired 95% CI** (an interval that excludes 0 means the condition really changed how the model settles)

| model | condition | Δ median lag | Δ p90 lag | Δ revisions /100 (pooled) | Δ revisions /100 (median utt) | Δ unstable tail | Δ agree before end |
|---|---|---:|---:|---:|---:|---:|---:|
| parakeet-tdt-0.6b-v3 | pots_babble10 | +100 [+80, +100] ms | +620 [+540, +700] ms | +43.6 [+31.8, +55.7] | +2.7 [+0.0, +5.1] | +0.57 [+0.41, +0.75] | -0.07 [-0.08, -0.06] s |
