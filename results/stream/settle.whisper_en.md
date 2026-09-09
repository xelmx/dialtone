normaliser: `whisper_en`  prefixes: first 1.0 s, step 0.5 s  aligner: `qwen3-forced-aligner-0.6b`

**Settle metrics** (95% bootstrap CI over utterances; lags quantised by the step, read differences not absolutes)

| model | condition | n | median lag | p90 lag | lag defined | revisions /100 (pooled) | revisions /100 (median utt) | unstable tail | agree before end | stream RTF | ×audio | empty partials | exploded partials | max partial words |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| parakeet-tdt-0.6b-v3 | clean | 2620 | 100 ms [100, 100] | 580 ms [520, 600] | 98% | 49.3 [44.8, 54.3] | 33.3 [31.6, 33.3] | 0.50 [0.44, 0.56] | 0.40 s [0.38, 0.41] | 0.062 | 11.7 | 927 | 41 | 509 |
| parakeet-tdt-0.6b-v3 | pots_babble10 | 2620 | 200 ms [180, 200] | 1200 ms [1120, 1280] | 96% | 92.9 [82.3, 104.9] | 36.0 [33.3, 37.5] | 1.07 [0.92, 1.25] | 0.33 s [0.32, 0.34] | 0.063 | 11.7 | 1969 | 104 | 1019 |
| qwen3-asr-0.6b | clean | 2620 | 140 ms [120, 140] | 420 ms [420, 420] | 98% | 8.8 [8.3, 9.2] | 5.9 [5.6, 6.2] | 0.10 [0.10, 0.10] | 0.36 s [0.35, 0.36] | 0.202 | 11.7 | 0 | 0 | 96 |
| qwen3-asr-0.6b | pots_babble10 | 2620 | 160 ms [160, 180] | 500 ms [500, 520] | 96% | 20.2 [19.0, 21.5] | 12.5 [11.8, 13.0] | 0.16 [0.15, 0.16] | 0.31 s [0.30, 0.32] | 0.198 | 11.7 | 2 | 0 | 96 |
| whisper-turbo | clean | 2620 | 120 ms [120, 120] | 440 ms [440, 440] | 98% | 22.9 [20.5, 25.8] | 15.2 [14.3, 15.8] | 0.26 [0.23, 0.30] | 0.38 s [0.37, 0.39] | 0.366 | 11.7 | 13 | 9 | 444 |
| whisper-turbo | pots_babble10 | 2620 | 160 ms [160, 160] | 620 ms [600, 620] | 95% | 45.7 [42.5, 49.1] | 32.3 [30.8, 33.3] | 0.48 [0.44, 0.52] | 0.32 s [0.31, 0.33] | 0.361 | 11.7 | 2 | 13 | 302 |

**Change vs clean, same utterances, paired 95% CI** (an interval that excludes 0 means the condition really changed how the model settles)

| model | condition | Δ median lag | Δ p90 lag | Δ revisions /100 (pooled) | Δ revisions /100 (median utt) | Δ unstable tail | Δ agree before end |
|---|---|---:|---:|---:|---:|---:|---:|
| parakeet-tdt-0.6b-v3 | pots_babble10 | +100 [+80, +100] ms | +620 [+540, +700] ms | +43.6 [+31.8, +55.7] | +2.7 [+0.0, +5.1] | +0.57 [+0.41, +0.75] | -0.07 [-0.08, -0.06] s |
| qwen3-asr-0.6b | pots_babble10 | +20 [+20, +40] ms | +80 [+80, +100] ms | +11.4 [+10.3, +12.8] | +6.6 [+5.9, +7.2] | +0.06 [+0.05, +0.06] | -0.04 [-0.05, -0.04] s |
| whisper-turbo | pots_babble10 | +40 [+40, +40] ms | +180 [+160, +180] ms | +22.8 [+18.9, +26.9] | +17.1 [+15.9, +19.0] | +0.22 [+0.17, +0.27] | -0.06 [-0.07, -0.05] s |
