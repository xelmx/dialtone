normaliser: `basic`  prefixes: first 1.0 s, step 0.5 s  aligner: `qwen3-forced-aligner-0.6b`

**Settle metrics** (95% bootstrap CI over utterances; lags quantised by the step, read differences not absolutes)

| model | condition | n | median lag | p90 lag | lag defined | revisions /100 (pooled) | revisions /100 (median utt) | unstable tail | agree before end | stream RTF | ×audio | empty partials | exploded partials | max partial words |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| whisper-turbo | clean | 2620 | 120 ms [120, 120] | 460 ms [440, 460] | 97% | 30.3 [27.6, 33.4] | 18.2 [17.4, 19.2] | 0.26 [0.23, 0.30] | 0.35 s [0.34, 0.36] | 0.366 | 11.7 | 13 | 9 | 444 |
| whisper-turbo | pots_babble10 | 2620 | 160 ms [160, 160] | 620 ms [600, 640] | 94% | 44.3 [41.0, 47.9] | 30.0 [28.6, 31.2] | 0.44 [0.40, 0.49] | 0.32 s [0.31, 0.33] | 0.361 | 11.7 | 2 | 14 | 302 |

**Change vs clean, same utterances, paired 95% CI** (an interval that excludes 0 means the condition really changed how the model settles)

| model | condition | Δ median lag | Δ p90 lag | Δ revisions /100 (pooled) | Δ revisions /100 (median utt) | Δ unstable tail | Δ agree before end |
|---|---|---:|---:|---:|---:|---:|---:|
| whisper-turbo | pots_babble10 | +40 [+40, +40] ms | +160 [+140, +180] ms | +14.0 [+9.9, +18.2] | +11.8 [+10.6, +13.2] | +0.18 [+0.13, +0.24] | -0.03 [-0.04, -0.02] s |
