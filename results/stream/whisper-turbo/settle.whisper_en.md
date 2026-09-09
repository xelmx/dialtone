normaliser: `whisper_en`  prefixes: first 1.0 s, step 0.5 s  aligner: `qwen3-forced-aligner-0.6b`

**Settle metrics** (95% bootstrap CI over utterances; lags quantised by the step, read differences not absolutes)

| model | condition | n | median lag | p90 lag | lag defined | revisions /100 (pooled) | revisions /100 (median utt) | unstable tail | agree before end | stream RTF | ×audio | empty partials | exploded partials | max partial words |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| whisper-turbo | clean | 2620 | 120 ms [120, 120] | 440 ms [440, 440] | 98% | 22.9 [20.5, 25.8] | 15.2 [14.3, 15.8] | 0.26 [0.23, 0.30] | 0.38 s [0.37, 0.39] | 0.366 | 11.7 | 13 | 9 | 444 |
| whisper-turbo | pots_babble10 | 2620 | 160 ms [160, 160] | 620 ms [600, 620] | 95% | 45.7 [42.5, 49.1] | 32.3 [30.8, 33.3] | 0.48 [0.44, 0.52] | 0.32 s [0.31, 0.33] | 0.361 | 11.7 | 2 | 13 | 302 |

**Change vs clean, same utterances, paired 95% CI** (an interval that excludes 0 means the condition really changed how the model settles)

| model | condition | Δ median lag | Δ p90 lag | Δ revisions /100 (pooled) | Δ revisions /100 (median utt) | Δ unstable tail | Δ agree before end |
|---|---|---:|---:|---:|---:|---:|---:|
| whisper-turbo | pots_babble10 | +40 [+40, +40] ms | +180 [+160, +180] ms | +22.8 [+18.9, +26.9] | +17.1 [+15.9, +19.0] | +0.22 [+0.17, +0.27] | -0.06 [-0.07, -0.05] s |
