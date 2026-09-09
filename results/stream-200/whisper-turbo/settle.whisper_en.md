normaliser: `whisper_en`  prefixes: first 1.0 s, step 0.5 s  aligner: `qwen3-forced-aligner-0.6b`

**Settle metrics** (95% bootstrap CI over utterances; lags quantised by the step, read differences not absolutes)

| model | condition | n | median lag | p90 lag | lag defined | revisions /100 (pooled) | revisions /100 (median utt) | unstable tail | agree before end | stream RTF | ×audio | empty partials | exploded partials | max partial words |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| whisper-turbo | clean | 200 | 100 ms [100, 120] | 440 ms [420, 461] | 98% | 21.9 [16.9, 28.7] | 15.0 [12.5, 16.7] | 0.20 [0.18, 0.22] | 0.36 s [0.32, 0.39] | 0.374 | 12.4 | 1 | 0 | 77 |
| whisper-turbo | pots_babble10 | 200 | 160 ms [140, 160] | 620 ms [540, 700] | 96% | 44.3 [34.5, 58.4] | 28.9 [25.0, 31.8] | 0.44 [0.35, 0.62] | 0.31 s [0.28, 0.35] | 0.377 | 12.4 | 1 | 1 | 148 |

**Change vs clean, same utterances, paired 95% CI** (an interval that excludes 0 means the condition really changed how the model settles)

| model | condition | Δ median lag | Δ p90 lag | Δ revisions /100 (pooled) | Δ revisions /100 (median utt) | Δ unstable tail | Δ agree before end |
|---|---|---:|---:|---:|---:|---:|---:|
| whisper-turbo | pots_babble10 | +60 [+20, +60] ms | +180 [+100, +260] ms | +22.4 [+12.6, +35.0] | +13.9 [+10.3, +17.2] | +0.24 [+0.14, +0.41] | -0.04 [-0.08, -0.01] s |
