normaliser: `whisper_en`  prefixes: first 1.0 s, step 0.5 s  aligner: `qwen3-forced-aligner-0.6b`

**Settle metrics** (95% bootstrap CI over utterances; lags quantised by the step, read differences not absolutes)

| model | condition | n | median lag | p90 lag | lag defined | revisions /100 (pooled) | revisions /100 (median utt) | unstable tail | agree before end | stream RTF | ×audio | empty partials | exploded partials | max partial words |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| parakeet-tdt-0.6b-v3 | clean | 200 | 80 ms [80, 100] | 520 ms [440, 680] | 98% | 40.4 [31.2, 53.3] | 30.0 [26.7, 33.3] | 0.40 [0.30, 0.55] | 0.40 s [0.37, 0.43] | 0.069 | 12.4 | 54 | 2 | 166 |
| parakeet-tdt-0.6b-v3 | pots_babble10 | 200 | 160 ms [160, 180] | 960 ms [780, 1180] | 96% | 78.1 [44.7, 123.2] | 31.6 [26.7, 36.4] | 0.89 [0.39, 1.55] | 0.35 s [0.31, 0.38] | 0.355 | 12.4 | 118 | 4 | 816 |

**Change vs clean, same utterances, paired 95% CI** (an interval that excludes 0 means the condition really changed how the model settles)

| model | condition | Δ median lag | Δ p90 lag | Δ revisions /100 (pooled) | Δ revisions /100 (median utt) | Δ unstable tail | Δ agree before end |
|---|---|---:|---:|---:|---:|---:|---:|
| parakeet-tdt-0.6b-v3 | pots_babble10 | +80 [+60, +100] ms | +440 [+200, +700] ms | +37.6 [+1.5, +83.0] | +1.6 [-4.0, +7.8] | +0.49 [-0.02, +1.18] | -0.06 [-0.09, -0.02] s |
